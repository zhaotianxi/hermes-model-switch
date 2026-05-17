from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml as _pyyaml

try:
    from ruamel.yaml import YAML
    _ruamel = YAML()
    _ruamel.preserve_quotes = True
    _ruamel.width = 4096
    HAS_RUAMEL = True
except ImportError:
    _ruamel = None
    HAS_RUAMEL = False


DEFAULT_HERMES_DIR = Path.home() / ".hermes"


def hermes_paths(hermes_dir: Path | None = None) -> dict:
    root = Path(hermes_dir or DEFAULT_HERMES_DIR)
    return {
        "root": root,
        "config": root / "config.yaml",
        "env": root / ".env",
        "backups": root / "backups",
        "lock": root / ".model-switch.lock",
    }


def load_yaml(path: Path) -> Any:
    if HAS_RUAMEL and _ruamel is not None:
        with open(path, "r", encoding="utf-8") as f:
            return _ruamel.load(f)
    with open(path, "r", encoding="utf-8") as f:
        return _pyyaml.safe_load(f) or {}


def save_yaml(path: Path, data) -> None:
    if HAS_RUAMEL and _ruamel is not None:
        with open(path, "w", encoding="utf-8") as f:
            _ruamel.dump(data, f)
        return
    path.write_text(_pyyaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def load_env_file(path: Path) -> dict[str, str]:
    env = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def resolve_var(value, env: dict[str, str]):
    if not isinstance(value, str):
        return value
    while True:
        match = re.search(r"\$\{([^}]+)\}", value)
        if not match:
            return value
        value = value.replace(match.group(0), env.get(match.group(1), ""))


def get_scalar(value):
    return getattr(value, "value", value)
