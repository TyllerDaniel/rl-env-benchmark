"""Sandboxes give an agent a shell inside a task's workspace.

Two implementations share one interface:

* DockerSandbox: one container per run, no network, CPU/memory/PID limits.
  The repo is copied in at start; the hidden grader is copied in only at
  grading time, so the agent can never read it.
* LocalSandbox: a throwaway copy of the repo on the host. Fast and needs no
  Docker, but it is NOT isolated. Use it for developing tasks and for the
  golden/no-op validation in CI, never for untrusted agents.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from .task import Task

MAX_OUTPUT_CHARS = 12_000


@dataclass
class ExecResult:
    exit_code: int
    output: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    def render(self) -> str:
        status = "timed out" if self.timed_out else f"exit code {self.exit_code}"
        return f"[{status}]\n{self.output}"


def truncate(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    """Keep the head and tail of long output; errors usually live at the end."""
    if len(text) <= limit:
        return text
    half = limit // 2
    return f"{text[:half]}\n... [{len(text) - limit} characters truncated] ...\n{text[-half:]}"


def run_process(
    argv: list[str],
    cwd: Path | None,
    timeout_s: int,
    env: dict[str, str] | None = None,
) -> ExecResult:
    """Run a command, killing its whole process group on timeout.

    subprocess.run(timeout=...) only kills the direct child. If that child
    spawned grandchildren (sh -> pytest), they keep the output pipe open and
    the call hangs anyway. Starting a new session and killing the group fixes it.
    """
    proc = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        start_new_session=True,
    )
    try:
        output, _ = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        output, _ = proc.communicate()
        return ExecResult(124, truncate(output or ""), timed_out=True)
    return ExecResult(proc.returncode, truncate(output or ""))


class Sandbox:
    """Base interface. Use as a context manager so cleanup always runs."""

    def __init__(self, task: Task):
        self.task = task

    def __enter__(self) -> "Sandbox":
        self.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def start(self) -> None:
        raise NotImplementedError

    def exec(self, command: str, timeout_s: int = 60) -> ExecResult:
        raise NotImplementedError

    def put_file(self, src: Path, dest: str) -> None:
        """Copy a host file to `dest`, relative to the workspace root."""
        raise NotImplementedError

    def grade(self) -> ExecResult:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class LocalSandbox(Sandbox):
    def __init__(self, task: Task):
        super().__init__(task)
        self._tmp: tempfile.TemporaryDirectory | None = None

    @property
    def base(self) -> Path:
        if self._tmp is None:
            raise RuntimeError("sandbox not started")
        return Path(self._tmp.name)

    @property
    def workspace(self) -> Path:
        return self.base / "workspace"

    def start(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix=f"rlbench-{self.task.id}-")
        shutil.copytree(self.task.repo_dir, self.workspace)

    def exec(self, command: str, timeout_s: int = 60) -> ExecResult:
        return run_process(["sh", "-c", command], cwd=self.workspace, timeout_s=timeout_s)

    def put_file(self, src: Path, dest: str) -> None:
        target = self.workspace / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)

    def grade(self) -> ExecResult:
        # The grader sits beside the workspace, not inside it.
        grader = self.base / "grader"
        shutil.copytree(self.task.grader_dir, grader, dirs_exist_ok=True)
        env = {**os.environ, "GRADER_DIR": str(grader)}
        return run_process(
            ["sh", str(grader / "grade.sh")],
            cwd=self.workspace,
            timeout_s=self.task.timeout_s,
            env=env,
        )

    def close(self) -> None:
        if self._tmp is not None:
            self._tmp.cleanup()
            self._tmp = None


def docker(*args: str, timeout_s: int = 600) -> ExecResult:
    return run_process(["docker", *args], cwd=None, timeout_s=timeout_s)


def ensure_image(kind: str, images_dir: Path) -> str:
    """Build images/<kind>/Dockerfile once and reuse it as rlbench-<kind>:latest."""
    tag = f"rlbench-{kind}:latest"
    if docker("image", "inspect", tag, timeout_s=30).ok:
        return tag
    context = images_dir / kind
    if not (context / "Dockerfile").is_file():
        raise FileNotFoundError(f"no Dockerfile for image '{kind}' in {context}")
    built = docker("build", "-t", tag, str(context), timeout_s=1200)
    if not built.ok:
        raise RuntimeError(f"docker build failed for {tag}:\n{built.output}")
    return tag


class DockerSandbox(Sandbox):
    WORKDIR = "/workspace"
    GRADER_DIR = "/grader"

    def __init__(self, task: Task, images_dir: Path, memory: str = "1g", cpus: str = "1"):
        super().__init__(task)
        self.images_dir = Path(images_dir)
        self.memory = memory
        self.cpus = cpus
        self.name = f"rlbench-{task.id}-{uuid.uuid4().hex[:8]}"
        self._running = False

    def _check(self, result: ExecResult, what: str) -> None:
        if not result.ok:
            raise RuntimeError(f"{what} failed:\n{result.output}")

    def start(self) -> None:
        image = ensure_image(self.task.image, self.images_dir)
        self._check(
            docker(
                "run", "-d", "--name", self.name,
                "--network", "none",
                "--memory", self.memory,
                "--cpus", self.cpus,
                "--pids-limit", "256",
                image, "sleep", "infinity",
            ),
            "docker run",
        )
        self._running = True
        self._check(
            docker("cp", f"{self.task.repo_dir}/.", f"{self.name}:{self.WORKDIR}"),
            "copying repo into container",
        )

    def _exec(self, command: list[str], timeout_s: int, env: dict[str, str] | None = None) -> ExecResult:
        argv = ["exec", "-w", self.WORKDIR]
        for key, value in (env or {}).items():
            argv += ["-e", f"{key}={value}"]
        # `timeout` inside the container kills the command itself; the outer
        # timeout is only a safety net in case docker exec hangs.
        argv += [self.name, "timeout", "-s", "KILL", str(timeout_s), *command]
        result = docker(*argv, timeout_s=timeout_s + 15)
        if result.exit_code == 137:  # killed by the inner timeout
            result.timed_out = True
        return result

    def exec(self, command: str, timeout_s: int = 60) -> ExecResult:
        return self._exec(["sh", "-c", command], timeout_s)

    def put_file(self, src: Path, dest: str) -> None:
        self._check(
            docker("cp", str(src), f"{self.name}:{self.WORKDIR}/{dest}"),
            f"copying {src.name} into container",
        )

    def grade(self) -> ExecResult:
        self._check(
            docker("cp", f"{self.task.grader_dir}/.", f"{self.name}:{self.GRADER_DIR}"),
            "copying grader into container",
        )
        return self._exec(
            ["sh", f"{self.GRADER_DIR}/grade.sh"],
            timeout_s=self.task.timeout_s,
            env={"GRADER_DIR": self.GRADER_DIR},
        )

    def close(self) -> None:
        if self._running:
            docker("rm", "-f", self.name, timeout_s=60)
            self._running = False
