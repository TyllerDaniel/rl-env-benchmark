"""Command line entry point: rlbench list | validate | run."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .agents import make_agent
from .runner import SANDBOX_KINDS, run_task, summarize, validate_task
from .task import Task, default_tasks_dir, discover


def _select(tasks: list[Task], ids: list[str] | None) -> list[Task]:
    if not ids:
        return tasks
    by_id = {t.id: t for t in tasks}
    unknown = [i for i in ids if i not in by_id]
    if unknown:
        raise SystemExit(f"unknown task id(s): {', '.join(unknown)}")
    return [by_id[i] for i in ids]


def cmd_list(tasks: list[Task], _args) -> int:
    for t in tasks:
        print(f"{t.id:32} {t.difficulty:7} {t.category:12} {t.title}")
    return 0


def github_annotation(title: str, message: str) -> str:
    """A workflow command that GitHub Actions shows as an error on the commit."""
    escaped = message[-4000:].replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return f"::error title={title}::{escaped}"


def cmd_validate(tasks: list[Task], args) -> int:
    in_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    failures = 0
    for t in tasks:
        problems = validate_task(t, args.sandbox, args.images_dir)
        if problems:
            failures += 1
            print(f"FAIL  {t.id}")
            for p in problems:
                print("      " + p.replace("\n", "\n      "))
                if in_actions:
                    print(github_annotation(f"Task {t.id} is invalid ({args.sandbox})", p))
        else:
            print(f"ok    {t.id}  (unsolved as shipped, golden fix passes)")
    print(f"\n{len(tasks) - failures}/{len(tasks)} tasks valid")
    return 1 if failures else 0


def cmd_run(tasks: list[Task], args) -> int:
    agent = make_agent(args.agent, model=args.model)
    results = []
    for t in tasks:
        print(f"running {t.id} with {agent.name} ...", flush=True)
        result = run_task(t, agent, args.sandbox, args.images_dir)
        results.append(result)
        print(f"  {'PASS' if result.passed else 'FAIL'} in {result.seconds}s, {result.steps} steps")
        if result.error:
            print(f"  error: {result.error}")
    print()
    print(summarize(results))
    if args.out:
        Path(args.out).write_text(json.dumps([r.to_dict() for r in results], indent=2))
        print(f"\nwrote {args.out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rlbench", description=__doc__)
    parser.add_argument("--tasks-dir", type=Path, default=None, help="directory of tasks (default: ./tasks)")
    parser.add_argument("--images-dir", type=Path, default=None, help="directory of base images (default: next to tasks)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list tasks")

    for name, help_text in (("validate", "check every task is unsolved as shipped and solvable"),
                            ("run", "run an agent against tasks and grade it")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--sandbox", choices=SANDBOX_KINDS, default="docker")
        p.add_argument("--task", action="append", dest="task_ids", help="task id (repeatable)")

    run = sub.choices["run"]
    run.add_argument("--agent", choices=("claude", "golden", "noop"), default="claude")
    run.add_argument("--model", default=None, help="model id for the claude agent (or set RLBENCH_MODEL)")
    run.add_argument("--out", default=None, help="write JSON results here")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    tasks_dir = args.tasks_dir or default_tasks_dir()
    args.images_dir = args.images_dir or tasks_dir.parent / "images"
    tasks = _select(discover(tasks_dir), getattr(args, "task_ids", None))
    handler = {"list": cmd_list, "validate": cmd_validate, "run": cmd_run}[args.command]
    return handler(tasks, args)


if __name__ == "__main__":
    sys.exit(main())
