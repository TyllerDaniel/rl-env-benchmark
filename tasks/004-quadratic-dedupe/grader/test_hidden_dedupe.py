import random
import signal
import time

import pytest

from ingest.dedupe import dedupe_events


@pytest.fixture
def deadline():
    """Fail fast instead of hanging if the implementation is still quadratic."""

    def _expired(signum, frame):
        raise TimeoutError("dedupe_events exceeded the time budget")

    previous = signal.signal(signal.SIGALRM, _expired)
    signal.alarm(10)
    yield
    signal.alarm(0)
    signal.signal(signal.SIGALRM, previous)


def make_events(n, distinct, seed=7):
    rng = random.Random(seed)
    return [
        {"user_id": rng.randrange(distinct // 50 + 1), "event_id": rng.randrange(distinct), "seq": i}
        for i in range(n)
    ]


def reference(events):
    seen, out = set(), []
    for e in events:
        k = (e["user_id"], e["event_id"])
        if k not in seen:
            seen.add(k)
            out.append(e)
    return out


def test_keeps_first_occurrence_in_order():
    events = make_events(2_000, 500)
    assert dedupe_events(events) == reference(events)


def test_accepts_generators():
    events = make_events(1_000, 300)
    assert dedupe_events(e for e in events) == reference(events)


def test_does_not_mutate_input():
    events = make_events(500, 100)
    snapshot = [dict(e) for e in events]
    dedupe_events(events)
    assert events == snapshot


def test_returns_a_list():
    assert dedupe_events([]) == []
    assert isinstance(dedupe_events(iter([])), list)


def test_large_batch_is_fast(deadline):
    events = make_events(300_000, 150_000)
    started = time.perf_counter()
    result = dedupe_events(events)
    elapsed = time.perf_counter() - started
    assert result == reference(events)
    assert elapsed < 2.0, f"took {elapsed:.2f}s for 300k events"
