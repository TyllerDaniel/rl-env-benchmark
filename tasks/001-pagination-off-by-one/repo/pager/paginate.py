"""Pagination helpers used by the list endpoints."""

from typing import List, Sequence, TypeVar

T = TypeVar("T")


def page_count(total: int, per_page: int) -> int:
    """Number of pages needed to show `total` items, `per_page` at a time."""
    if per_page <= 0:
        raise ValueError("per_page must be positive")
    if total < 0:
        raise ValueError("total cannot be negative")
    return total // per_page


def paginate(items: Sequence[T], page: int, per_page: int) -> List[T]:
    """Return the items on a 1-indexed `page`. Pages past the end are empty."""
    if page < 1:
        raise ValueError("pages are 1-indexed")
    if page > page_count(len(items), per_page):
        return []
    start = page * per_page
    return list(items[start:start + per_page])
