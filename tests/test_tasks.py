"""Every task must be well formed, unsolved as shipped, and solvable by its golden fix."""

import pytest

from rlbench.runner import validate_task
from rlbench.task import discover

from conftest import IMAGES_DIR, TASKS_DIR

ALL_TASKS = discover(TASKS_DIR)


def test_tasks_are_discovered():
    assert len(ALL_TASKS) >= 5


def test_ids_are_unique_and_match_directories():
    ids = [t.id for t in ALL_TASKS]
    assert len(ids) == len(set(ids))
    for t in ALL_TASKS:
        assert t.root.name == t.id


@pytest.mark.parametrize("task", ALL_TASKS, ids=lambda t: t.id)
def test_task_metadata(task):
    assert len(task.prompt) > 80, "prompt should give the agent enough context"
    assert (IMAGES_DIR / task.image / "Dockerfile").is_file()


@pytest.mark.parametrize("task", ALL_TASKS, ids=lambda t: t.id)
def test_grader_is_not_shipped_in_repo(task):
    hidden = {p.name for p in task.grader_dir.iterdir()}
    shipped = {p.name for p in task.repo_dir.rglob("*")}
    assert not hidden & shipped - {"grade.sh"}, "hidden test files leaked into the repo"


@pytest.mark.parametrize("task", ALL_TASKS, ids=lambda t: t.id)
def test_task_is_valid_locally(task):
    assert validate_task(task, "local", IMAGES_DIR) == []


def test_github_annotation_escapes_newlines():
    from rlbench.cli import github_annotation

    line = github_annotation("Task x", "first\nsecond 100%")
    assert line == "::error title=Task x::first%0Asecond 100%25"
