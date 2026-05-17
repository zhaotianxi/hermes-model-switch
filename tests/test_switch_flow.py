from hermes_model_switch import cli


def test_list_command(capsys):
    assert cli.main(["list"]) == 0
    out = capsys.readouterr().out
    assert "gpt" in out


def test_dry_run_switch(tmp_path, capsys, monkeypatch):
    hermes_dir = tmp_path / ".hermes"
    hermes_dir.mkdir()
    (hermes_dir / ".env").write_text("MODELVERSE_API_KEY_GPT=test-gpt\n", encoding="utf-8")
    (hermes_dir / "config.yaml").write_text(
        "model:\n  default: gpt-5.4\n  provider: custom:modelverse-gpt\n  base_url: https://api.modelverse.cn/v1\n  api_key: ${MODELVERSE_API_KEY_GPT}\n\ncustom_providers:\n  - name: modelverse-gpt\n    base_url: https://api.modelverse.cn/v1\n    api_key: ${MODELVERSE_API_KEY_GPT}\n    model: gpt-5.4\n    models:\n      gpt-5.4:\n        context_length: 200000\n\nmodel_aliases:\n  gpt:\n    provider: custom:modelverse-gpt\n    base_url: https://api.modelverse.cn/v1\n    model: gpt-5.4\n    api_key: ${MODELVERSE_API_KEY_GPT}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "verify_model", lambda *args, **kwargs: (True, ""))
    assert cli.main(["--hermes-dir", str(hermes_dir), "switch", "gpt", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert '"action": "dry-run"' in out
    assert '"target_mode": "gpt"' in out
