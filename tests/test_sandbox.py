import time

from rlbench.sandbox import LocalSandbox, run_process, truncate


def test_truncate_keeps_head_and_tail():
    text = "HEAD" + "x" * 50_000 + "TAIL"
    out = truncate(text, limit=1_000)
    assert out.startswith("HEAD") and out.endswith("TAIL")
    assert "characters truncated" in out
    assert len(out) < 1_200


def test_truncate_leaves_short_text_alone():
    assert truncate("short", limit=100) == "short"


def test_timeout_kills_grandchildren():
    # Without process-group killing, the backgrounded sleep keeps the pipe open
    # and this call would block for the full 30 seconds.
    started = time.monotonic()
    result = run_process(["sh", "-c", "sleep 30 & sleep 30"], cwd=None, timeout_s=1)
    assert result.timed_out
    assert time.monotonic() - started < 10


def test_exec_reports_exit_code_and_output(tasks):
    with LocalSandbox(tasks[0]) as sb:
        result = sb.exec("echo hello; exit 3")
    assert result.exit_code == 3
    assert "hello" in result.output
    assert not result.ok


def test_grader_is_invisible_to_the_agent(tasks):
    task = tasks[0]
    with LocalSandbox(task) as sb:
        listing = sb.exec("ls -aR").output
        for hidden in task.grader_dir.iterdir():
            if hidden.name != "grade.sh":
                assert hidden.name not in listing


def test_workspace_is_a_copy(tasks):
    task = tasks[0]
    with LocalSandbox(task) as sb:
        sb.exec("echo changed > pager/paginate.py")
    assert "def paginate" in (task.repo_dir / "pager" / "paginate.py").read_text()


def test_grader_refuses_sitecustomize(tasks):
    python_task = next(t for t in tasks if t.image == "python")
    with LocalSandbox(python_task) as sb:
        sb.exec("echo 'import sys' > sitecustomize.py")
        result = sb.grade()
    assert result.exit_code == 2
    assert "refusing to grade" in result.output
