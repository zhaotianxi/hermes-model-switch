import json

from hermes_model_switch.backup import create_backup, find_latest_valid_backup, list_backups


def test_create_and_list_backups(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("model:\n  default: gpt-5.4\n", encoding="utf-8")
    backups = tmp_path / "backups"

    backup_id, config_backup, meta_backup = create_backup(config, backups, "gpt-5.4", "glm")

    assert config_backup.exists()
    assert meta_backup.exists()
    meta = json.loads(meta_backup.read_text(encoding="utf-8"))
    assert meta["backup_id"] == backup_id
    assert meta["source_default"] == "gpt-5.4"
    assert meta["target_mode"] == "glm"

    items = list_backups(backups)
    assert len(items) == 1
    assert items[0]["backup_id"] == backup_id


def test_find_latest_valid_backup(tmp_path):
    backups = tmp_path / "backups"
    backups.mkdir()
    for idx, default in enumerate(["gpt-5.4", "GLM-5.1"]):
        folder = backups / f"20260517T00000{idx}Z-gpt"
        folder.mkdir()
        (folder / "config.yaml").write_text(f"model:\n  default: {default}\n", encoding="utf-8")
        (folder / "meta.json").write_text(json.dumps({"backup_id": folder.name}), encoding="utf-8")
    hit = find_latest_valid_backup(backups, "GLM-5.1")
    assert hit is not None
    assert hit["config_default"] == "GLM-5.1"
