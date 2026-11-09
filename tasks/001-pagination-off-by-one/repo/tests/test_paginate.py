import pytest

from pager import page_count, paginate


def test_page_count_exact_multiple():
    assert page_count(10, 5) == 2


def test_rejects_zero_per_page():
    with pytest.raises(ValueError):
        page_count(10, 0)


def test_page_zero_is_invalid():
    with pytest.raises(ValueError):
        paginate([1, 2, 3], 0, 2)
