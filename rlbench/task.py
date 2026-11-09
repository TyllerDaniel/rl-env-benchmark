"""Task definitions. Each task is a directory under tasks/:

    task.toml       metadata and the prompt the agent sees
    repo/           the starting repository (broken on purpose)
    grader/         hidden grader; grade.sh exits 0 on success
    solution.patch  golden reference fix, applied with `patch -p1`
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

REQUIRED_FIELDS = ("id", "title", "category", "difficulty", "image", "prompt")
DIFFICULTIES = ("easy", "medium", "hard")


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    category: str
    difficulty: str
    image: str
    prompt: str
    root: Path
    timeout_s: int = 120

    @property
    def repo_dir(self) -> Path:
        return self.root / "repo"

    @property
    def grader_dir(self) -> Path:
        return self.root / "grader"

    @property
    def solution_patch(self) -> Path:
        return self.root / "solution.patch"

    @classmethod
    def load(cls, root: Path) -> "Task":
        root = Path(root)
        data = tomllib.loads((root / "task.toml").read_text())

        missing = [field for field in REQUIRED_FIELDS if field not in data]
        if missing:
            raise ValueError(f"{root}: task.toml is missing {', '.join(missing)}")
        if data["difficulty"] not in DIFFICULTIES:
            raise ValueError(f"{root}: difficulty must be one of {DIFFICULTIES}")

        task = cls(
            id=data["id"],
            title=data["title"],
            category=data["category"],
            difficulty=data["difficulty"],
            image=data["image"],
            prompt=data["prompt"].strip(),
            root=root,
            timeout_s=int(data.get("timeout_s", 120)),
        )
        for required in (task.repo_dir, task.grader_dir / "grade.sh", task.solution_patch):
            if not required.exists():
                raise ValueError(f"{task.id}: missing {required.relative_to(root)}")
        return task


def default_tasks_dir() -> Path:
    """./tasks when run from a checkout, otherwise the directory next to the package."""
    cwd_tasks = Path.cwd() / "tasks"
    if cwd_tasks.is_dir():
        return cwd_tasks
    return Path(__file__).resolve().parent.parent / "tasks"


def discover(tasks_dir: Path | None = None) -> list[Task]:
    tasks_dir = Path(tasks_dir or default_tasks_dir())
    return [
        Task.load(path)
        for path in sorted(tasks_dir.iterdir())
        if (path / "task.toml").is_file()
    ]
