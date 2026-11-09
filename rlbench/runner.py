"""Run agents against tasks, grade the result, and validate task quality."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .agents import Agent, GoldenAgent, NoopAgent
from .sandbox import DockerSandbox, LocalSandbox, Sandbox
from .task import Task

SANDBOX_KINDS = ("docker", "local")


@dataclass
class RunResult:
    task_id: str
    agent: str
    passed: bool
    steps: int
    seconds: float
    grader_output: str
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def make_sandbox(task: Task, kind: str, images_dir: Path) -> Sandbox:
    if kind == "docker":
        return DockerSandbox(task, images_dir)
    if kind == "local":
        return LocalSandbox(task)
    raise ValueError(f"unknown sandbox '{kind}', expected one of {SANDBOX_KINDS}")


def run_task(task: Task, agent: Agent, sandbox_kind: str, images_dir: Path) -> RunResult:
    started = time.monotonic()
    steps = 0
    try:
        with make_sandbox(task, sandbox_kind, images_dir) as sandbox:
            trace = agent.solve(task, sandbox)
            steps = trace.steps
            graded = sandbox.grade()
    except Exception as exc:  # an agent or sandbox crash is a failed run, not a crashed benchmark
        return RunResult(
            task_id=task.id,
            agent=agent.name,
            passed=False,
            steps=steps,
            seconds=round(time.monotonic() - started, 2),
            grader_output="",
            error=f"{type(exc).__name__}: {exc}",
        )
    return RunResult(
        task_id=task.id,
        agent=agent.name,
        passed=graded.ok,
        steps=steps,
        seconds=round(time.monotonic() - started, 2),
        grader_output=graded.output,
    )


def validate_task(task: Task, sandbox_kind: str, images_dir: Path) -> list[str]:
    """A task is only useful if it is unsolved as shipped and solvable by the golden fix."""
    problems = []

    baseline = run_task(task, NoopAgent(), sandbox_kind, images_dir)
    if baseline.error:
        problems.append(f"no-op run crashed: {baseline.error}")
    elif baseline.passed:
        problems.append("grader passes on the untouched repo, so the task is already solved")

    golden = run_task(task, GoldenAgent(), sandbox_kind, images_dir)
    if not golden.passed:
        detail = golden.error or golden.grader_output
        problems.append(f"golden solution fails the grader:\n{detail}")

    return problems


def summarize(results: list[RunResult]) -> str:
    """Markdown table for reports and the README."""
    lines = [
        "| Task | Agent | Result | Steps | Time (s) |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in results:
        verdict = "pass" if r.passed else ("error" if r.error else "fail")
        lines.append(f"| {r.task_id} | {r.agent} | {verdict} | {r.steps} | {r.seconds} |")
    passed = sum(r.passed for r in results)
    lines.append("")
    lines.append(f"Passed {passed}/{len(results)}")
    return "\n".join(lines)
