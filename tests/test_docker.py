"""Full validation inside Docker. Opt in with RLBENCH_DOCKER_TESTS=1 (CI does)."""

import os

import pytest

from rlbench.runner import validate_task
from rlbench.task import discover

from conftest import IMAGES_DIR, TASKS_DIR

pytestmark = [
    pytest.mark.docker,
    pytest.mark.skipif(os.environ.get("RLBENCH_DOCKER_TESTS") != "1", reason="set RLBENCH_DOCKER_TESTS=1"),
]


@pytest.mark.parametrize("task", discover(TASKS_DIR), ids=lambda t: t.id)
def test_task_is_valid_in_docker(task):
    assert validate_task(task, "docker", IMAGES_DIR) == []
