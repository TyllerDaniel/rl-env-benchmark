"""Agents that attempt a task inside a sandbox.

* NoopAgent: changes nothing. Used to prove a task is not already solved.
* GoldenAgent: applies the reference solution. Used to prove a task is solvable.
* ClaudeAgent: a model with a single bash tool, looping until it stops calling tools.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Protocol

from .sandbox import Sandbox
from .task import Task

DEFAULT_MODEL = "claude-sonnet-5-5"


@dataclass
class AgentTrace:
    steps: int = 0
    transcript: list[str] = field(default_factory=list)


class Agent(Protocol):
    name: str

    def solve(self, task: Task, sandbox: Sandbox) -> AgentTrace: ...


class NoopAgent:
    name = "noop"

    def solve(self, task: Task, sandbox: Sandbox) -> AgentTrace:
        return AgentTrace()


class GoldenAgent:
    name = "golden"

    def solve(self, task: Task, sandbox: Sandbox) -> AgentTrace:
        sandbox.put_file(task.solution_patch, ".golden.patch")
        result = sandbox.exec("patch -p1 --forward --batch < .golden.patch && rm .golden.patch")
        if not result.ok:
            raise RuntimeError(f"golden patch did not apply to {task.id}:\n{result.output}")
        return AgentTrace(steps=1, transcript=[result.output])


SYSTEM_PROMPT = """\
You are a software engineer working in a repository at the current directory.
The sandbox has no network access. Use the bash tool to read, run and edit code.
Fix the root cause rather than the symptom, and do not edit or delete tests to make them pass.
When you are confident the task is complete, reply with a short summary and stop calling tools."""

BASH_TOOL = {
    "name": "bash",
    "description": (
        "Run a shell command from the repository root. Returns the exit code "
        "and combined stdout/stderr, truncated if very long."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"command": {"type": "string", "description": "The command to run."}},
        "required": ["command"],
    },
}


class ClaudeAgent:
    name = "claude"

    def __init__(
        self,
        model: str | None = None,
        max_steps: int = 30,
        command_timeout_s: int = 60,
        client: Any = None,
    ):
        if client is None:
            import anthropic  # optional dependency: pip install 'rl-env-benchmark[claude]'

            client = anthropic.Anthropic()
        self.client = client
        self.model = model or os.environ.get("RLBENCH_MODEL", DEFAULT_MODEL)
        self.max_steps = max_steps
        self.command_timeout_s = command_timeout_s

    def solve(self, task: Task, sandbox: Sandbox) -> AgentTrace:
        trace = AgentTrace()
        messages: list[dict[str, Any]] = [{"role": "user", "content": task.prompt}]

        for _ in range(self.max_steps):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=[BASH_TOOL],
                messages=messages,
            )
            trace.steps += 1
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "text" and block.text.strip():
                    trace.transcript.append(f"assistant: {block.text.strip()}")
                elif block.type == "tool_use":
                    command = str(block.input.get("command", ""))
                    result = sandbox.exec(command, timeout_s=self.command_timeout_s)
                    trace.transcript.append(f"$ {command}\n{result.render()}")
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result.render(),
                            "is_error": not result.ok,
                        }
                    )

            if response.stop_reason != "tool_use" or not tool_results:
                break
            messages.append({"role": "user", "content": tool_results})

        return trace


def make_agent(name: str, model: str | None = None) -> Agent:
    if name == "noop":
        return NoopAgent()
    if name == "golden":
        return GoldenAgent()
    if name == "claude":
        return ClaudeAgent(model=model)
    raise ValueError(f"unknown agent '{name}'")
