from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .config_io import get_scalar, load_yaml, save_yaml
from .model_specs import mode_from_default


def create_backup(config_path: Path, backups_dir: Path, source_default: str, target_mode: str) -> tuple[str, Path, Path]:
    backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_id = f"{stamp}-{target_mode}"
    folder = backups_dir / backup_id
    folder.mkdir(parents=True, exist_ok=True)
    config_backup = folder / "config.yaml"
    meta_backup = folder / "meta.json"
    shutil.copy2(config_path, config_backup)
    metadata = {
        "backup_id": backup_id,
        "created_at": stamp,
        "source_default": source_default,
        "source_mode": mode_from_default(source_default),
        "target_mode": target_mode,
    }
    meta_backup.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return backup_id, config_backup, meta_backup


def list_backups(backups_dir: Path) -> list[dict]:
    if not backups_dir.exists():
        return []
    items = []
    for folder in sorted(backups_dir.iterdir(), reverse=True):
        if not folder.is_dir():
            continue
        meta = folder / "meta.json"
        conf = folder / "config.yaml"
        if not meta.exists() or not conf.exists():
            continue
        try:
            info = json.loads(meta.read_text(encoding="utf-8"))
            config = load_yaml(conf)
            info["config_default"] = get_scalar(config.get("model", {}).get("default", ""))
            items.append(info)
        except Exception:
            continue
    return items


def restore_backup(config_path: Path, backups_dir: Path, backup_id: str) -> Path:
    folder = backups_dir / backup_id
    backup_file = folder / "config.yaml"
    if not backup_file.exists():
        raise FileNotFoundError(f"backup not found: {backup_id}")
    shutil.copy2(backup_file, config_path)
    return backup_file


def find_latest_valid_backup(backups_dir: Path, expected_default: str, exclude_backup_id: str | None = None) -> dict | None:
    for item in list_backups(backups_dir):
        if exclude_backup_id and item.get("backup_id") == exclude_backup_id:
            continue
        if item.get("config_default") == expected_default:
            return item
    return None
