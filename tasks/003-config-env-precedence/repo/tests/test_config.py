from svc.config import DEFAULTS, load


def test_defaults_when_nothing_set():
    assert load(env={}) == DEFAULTS


def test_file_overrides_defaults():
    assert load({"workers": 4}, env={})["workers"] == 4
