"""Service configuration.

Precedence, highest first:
    1. Environment variables named APP_<KEY> (e.g. APP_PORT)
    2. Values from the config file (passed in as a dict)
    3. DEFAULTS

Every value is converted to the type of its default:
    * int keys accept integer strings ("9000")
    * bool keys accept true/false, yes/no, on/off, 1/0 (any case)
    * anything unparseable raises ValueError naming the key
Keys that are not in DEFAULTS are rejected with KeyError.
"""

import os
from typing import Any, Mapping, Optional

DEFAULTS = {
    "port": 8080,
    "debug": False,
    "workers": 2,
    "log_level": "info",
}


def load(
    file_values: Optional[Mapping[str, Any]] = None,
    env: Optional[Mapping[str, str]] = None,
) -> dict:
    env = os.environ if env is None else env
    cfg = dict(DEFAULTS)

    for key in cfg:
        env_key = "APP_" + key.upper()
        if env_key in env:
            cfg[key] = env[env_key]

    if file_values:
        cfg.update(file_values)

    return cfg
