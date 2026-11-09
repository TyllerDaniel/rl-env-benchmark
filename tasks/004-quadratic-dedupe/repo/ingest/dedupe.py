"""De-duplication for incoming analytics events."""

from typing import Dict, Iterable, List


def dedupe_events(events: Iterable[Dict]) -> List[Dict]:
    """Drop repeated (user_id, event_id) pairs, keeping the first occurrence in order."""
    seen = []
    unique = []
    for event in events:
        key = (event["user_id"], event["event_id"])
        if key not in seen:
            seen.append(key)
            unique.append(event)
    return unique
