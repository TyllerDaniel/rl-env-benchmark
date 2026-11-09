import pytest

from pager import page_count, paginate

ITEMS = list(range(1, 12))  # 11 items


@pytest.mark.parametrize(
    "total, per_page, expected",
    [(0, 5, 0), (1, 5, 1), (5, 5, 1), (10, 5, 2), (11, 5, 3), (11, 1, 11)],
)
def test_page_count(total, per_page, expected):
    assert page_count(total, per_page) == expected


def test_first_page():
    assert paginate(ITEMS, 1, 5) == [1, 2, 3, 4, 5]


def test_middle_page():
    assert paginate(ITEMS, 2, 5) == [6, 7, 8, 9, 10]


def test_partial_last_page():
    assert paginate(ITEMS, 3, 5) == [11]


def test_past_the_end_is_empty():
    assert paginate(ITEMS, 4, 5) == []


def test_every_item_appears_exactly_once():
    for per_page in range(1, 13):
        pages = [paginate(ITEMS, p, per_page) for p in range(1, page_count(len(ITEMS), per_page) + 1)]
        assert [x for page in pages for x in page] == ITEMS


def test_empty_input():
    assert paginate([], 1, 5) == []


def test_validation_still_enforced():
    with pytest.raises(ValueError):
        paginate(ITEMS, 0, 5)
    with pytest.raises(ValueError):
        page_count(5, 0)
