import pytest

from svc.config import DEFAULTS, load


def test_defaults():
    assert load(env={}) == DEFAULTS


def test_env_beats_file():
    cfg = load({"port": 7000}, env={"APP_PORT": "9000"})
    assert cfg["port"] == 9000


def test_file_beats_defaults():
    assert load({"log_level": "debug"}, env={})["log_level"] == "debug"


def test_env_int_is_coerced():
    cfg = load(env={"APP_PORT": "9000", "APP_WORKERS": "8"})
    assert cfg["port"] == 9000 and isinstance(cfg["port"], int)
    assert cfg["workers"] == 8


@pytest.mark.parametrize("raw", ["false", "False", "FALSE", "no", "off", "0"])
def test_env_false_values(raw):
    assert load({"debug": True}, env={"APP_DEBUG": raw})["debug"] is False


@pytest.mark.parametrize("raw", ["true", "True", "yes", "ON", "1"])
def test_env_true_values(raw):
    assert load(env={"APP_DEBUG": raw})["debug"] is True


def test_file_values_are_coerced_too():
    cfg = load({"port": "7000", "debug": "yes"}, env={})
    assert cfg["port"] == 7000
    assert cfg["debug"] is True


def test_bad_int_raises_value_error_naming_key():
    with pytest.raises(ValueError, match="port"):
        load(env={"APP_PORT": "eighty"})


def test_bad_bool_raises_value_error_naming_key():
    with pytest.raises(ValueError, match="debug"):
        load(env={"APP_DEBUG": "maybe"})


def test_unknown_file_key_rejected():
    with pytest.raises(KeyError):
        load({"prot": 9000}, env={})


def test_strings_stay_strings():
    assert load(env={"APP_LOG_LEVEL": "warning"})["log_level"] == "warning"


def test_unrelated_env_ignored():
    assert load(env={"PORT": "1", "APP_UNKNOWN": "x"}) == DEFAULTS


def test_defaults_not_mutated():
    before = dict(DEFAULTS)
    load({"workers": 9}, env={"APP_PORT": "1"})
    assert DEFAULTS == before
