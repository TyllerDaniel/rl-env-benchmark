from pathlib import Path

import pytest

from rlbench.task import discover

ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "tasks"
IMAGES_DIR = ROOT / "images"


@pytest.fixture(scope="session")
def tasks():
    return discover(TASKS_DIR)


@pytest.fixture(scope="session")
def images_dir():
    return IMAGES_DIR
