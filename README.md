# rl-env-benchmark

[![CI](https://github.com/TyllerDaniel/rl-env-benchmark/actions/workflows/ci.yml/badge.svg)](https://github.com/TyllerDaniel/rl-env-benchmark/actions/workflows/ci.yml)

Reproducible environments that test whether an AI coding agent can do real
software-engineering work: debugging, fixing flaky CI, untangling config,
performance tuning and memory safety. Each task ships a broken repository, a
prompt, a **hidden grader** and a **golden reference fix**.

The harness itself is small and dependency-free. It runs each task in an
isolated Docker container, lets an agent work through a bash tool, then grades
the result with tests the agent never saw.

## Tasks

| ID | Category | Difficulty | What the agent has to do |
| --- | --- | --- | --- |
| `001-pagination-off-by-one` | debugging | easy | Two interacting off-by-one bugs drop the last page and shift the first |
| `002-test-order-pollution` | ci-flake | medium | Tests pass or fail depending on order because a default dict is shared and mutated |
| `003-config-env-precedence` | devops | medium | Env vars lose to the config file and `"false"` is truthy; match the documented contract |
| `004-quadratic-dedupe` | performance | medium | An O(n²) list lookup times out at 300k events; fix it without changing behaviour |
| `005-asan-heap-overflow` | memory-safety | hard | A 1-byte heap overflow in C that the existing tests and `make asan` miss |

In every task the **visible tests pass on the broken code**. That is deliberate:
an agent that only runs the existing test suite and stops will fail. It has to
read the prompt, reproduce the real problem and fix the root cause.

## How it works

```
task.toml + repo/ ──► sandbox (Docker, no network) ──► agent works via bash
                                                              │
                         grader/ copied in only now ◄─────────┘
                                   │
                              grade.sh exit 0 = pass
```

* **Sandboxes.** `DockerSandbox` runs one container per attempt with
  `--network none`, CPU, memory and PID limits. The repo is copied in at start;
  the grader is copied in only after the agent finishes. `LocalSandbox` uses a
  temporary directory on the host for fast task development and CI. It is not
  isolated, so never point it at an untrusted agent.
* **Agents.** `noop` changes nothing, `golden` applies `solution.patch`, and
  `claude` is a model with one bash tool, looping until it stops calling tools
  or hits a step limit.
* **Validation.** `rlbench validate` enforces the two properties every task
  needs: the no-op agent must **fail** (the task is not already solved) and the
  golden agent must **pass** (the task is solvable and the grader is correct).

## Quick start

```bash
pip install -e '.[dev]'
rlbench list
rlbench validate --sandbox local     # fast, no Docker
rlbench validate                     # full check in Docker
pytest                               # harness tests
```

Run Claude against the tasks (needs `ANTHROPIC_API_KEY`):

```bash
pip install -e '.[claude]'
rlbench run --agent claude --out results.json
rlbench run --agent claude --task 005-asan-heap-overflow --model <model-id>
```

`run` prints a Markdown summary table and, with `--out`, writes per-task JSON
including the grader output, which shows exactly which hidden checks failed.

## Designing tasks that measure something

Lessons baked into these tasks:

* **Hide the grader, but make the prompt sufficient.** Everything the grader
  checks is stated or implied by the prompt or a docstring (for example, task
  003's contract lives in the module docstring). Hidden tests should catch
  incomplete fixes, not trick the agent.
* **Test behaviour, not text.** Graders exercise the public API across ranges
  of inputs (task 005 sweeps 64 capacities × 81 lengths) instead of diffing
  source files, so any correct fix passes.
* **Close the obvious shortcuts.** Graders run outside the workspace, so a
  `conftest.py` in the repo is never collected; Python graders refuse to run if
  the workspace contains `sitecustomize.py` or `usercustomize.py`, which could
  hijack the interpreter. The C grader compiles the agent's source against its
  own test file with `-fno-sanitize-recover=all`.
* **Fail fast.** The performance grader uses `SIGALRM` so a quadratic solution
  fails in 10 seconds instead of hanging the run.
* **Kill the whole process tree on timeout.** `subprocess.run(timeout=...)`
  only kills the direct child; a backgrounded grandchild keeps the pipe open and
  the call hangs. The sandbox starts each command in its own session and kills
  the process group (see `tests/test_sandbox.py::test_timeout_kills_grandchildren`).

## Adding a task

```
tasks/006-your-task/
  task.toml          # id, title, category, difficulty, image, prompt, timeout_s
  repo/              # starting state the agent sees
  grader/grade.sh    # runs from the workspace; $GRADER_DIR points at grader/
  grader/...         # hidden tests
  solution.patch     # `diff -ruN a b` against repo/, applied with patch -p1
```

Then run `rlbench validate --task 006-your-task`. Base images live in
`images/<name>/Dockerfile` and are built once on first use.

## Limitations

* The bash tool gives the agent full control of the container, so a determined
  agent could still tamper with the toolchain itself (for example by replacing
  `python3` in the image). A production version would grade in a fresh container
  built from the agent's diff only.
* Five tasks is a demonstration of the method, not a statistically meaningful
  benchmark.

## License

MIT
