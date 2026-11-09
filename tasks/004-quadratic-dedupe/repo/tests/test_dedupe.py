from ingest.dedupe import dedupe_events


def test_removes_duplicates_keeping_first():
    events = [
        {"user_id": 1, "event_id": "a", "n": 1},
        {"user_id": 1, "event_id": "a", "n": 2},
        {"user_id": 2, "event_id": "a", "n": 3},
    ]
    assert [e["n"] for e in dedupe_events(events)] == [1, 3]
