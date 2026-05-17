from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .backup import create_backup, find_latest_valid_backup, list_backups, restore_backup
from .config_io import get_scalar, hermes_paths, load_env_file, load_yaml, resolve_var, save_yaml
from .locking import file_lock
from .model_specs import (
    build_alias_update,
    build_main_model_config,
    build_provider_def,
    get_spec,
    iter_specs,
    mode_from_default,
)
from .verify import hermes_smoke_test, verify_model


def fail(message: str, code: int = 1) -> int:
    print(message, file=sys.stderr)
    return code


def mask(value: str) -> str:
    if not value:
        return "(empty)"
    return value[:6] + "..." + value[-4:] if len(value) > 10 else "***"


def _load_current_config(paths: dict):
    if not paths["config"].exists():
        raise FileNotFoundError(f"配置文件不存在: {paths['config']}")
    return load_yaml(paths["config"])


def _current_default(conf) -> str:
    return get_scalar(conf.get("model", {}).get("default", ""))


def _update_config(conf, spec: dict):
    conf.setdefault("model", {})
    conf.setdefault("custom_providers", [])
    conf.setdefault("model_aliases", {})

    conf["model"].update(build_main_model_config(spec))

    provider_def = build_provider_def(spec)
    providers = conf["custom_providers"]
    for idx, provider in enumerate(providers):
        if get_scalar(provider.get("name", "")) == provider_def["name"]:
            providers[idx] = provider_def
            break
    else:
        providers.append(provider_def)

    alias_key, alias_value = build_alias_update(spec)
    conf["model_aliases"].setdefault(alias_key, {})
    conf["model_aliases"][alias_key].update(alias_value)
    return conf


def _verify_written_config(conf, spec: dict) -> list[str]:
    errors = []
    model_conf = conf.get("model", {})
    expected_main = build_main_model_config(spec)
    for key in ("default", "provider", "api_key", "base_url"):
        actual = get_scalar(model_conf.get(key, ""))
        if actual != expected_main[key]:
            errors.append(f"model.{key} mismatch: expected={expected_main[key]} actual={actual}")

    provider_def = build_provider_def(spec)
    providers = conf.get("custom_providers", [])
    matched = None
    for provider in providers:
        if get_scalar(provider.get("name", "")) == provider_def["name"]:
            matched = provider
            break
    if not matched:
        errors.append(f"custom_providers missing provider {provider_def['name']}")
    else:
        for key in ("base_url", "api_key", "model"):
            actual = get_scalar(matched.get(key, ""))
            if actual != provider_def[key]:
                errors.append(f"custom_providers.{provider_def['name']}.{key} mismatch: expected={provider_def[key]} actual={actual}")

    alias_key, alias_value = build_alias_update(spec)
    aliases = conf.get("model_aliases", {})
    alias_conf = aliases.get(alias_key)
    if not alias_conf:
        errors.append(f"model_aliases missing alias {alias_key}")
    else:
        for key, expected in alias_value.items():
            actual = get_scalar(alias_conf.get(key, ""))
            if actual != expected:
                errors.append(f"model_aliases.{alias_key}.{key} mismatch: expected={expected} actual={actual}")
    return errors


def cmd_list(args) -> int:
    rows = []
    for mode, spec in iter_specs():
        rows.append({
            "mode": mode,
            "label": spec["label"],
            "default": spec["default"],
            "provider": spec["provider_ref"],
            "alias": spec["alias"],
        })
    print(json.dumps(rows, ensure_ascii=False, indent=2) if args.json else "\n".join(
        f"{r['mode']:8} {r['label']:28} {r['default']}" for r in rows
    ))
    return 0


def cmd_current(args) -> int:
    paths = hermes_paths(Path(args.hermes_dir) if args.hermes_dir else None)
    conf = _load_current_config(paths)
    default = _current_default(conf)
    mode = mode_from_default(default)
    payload = {"mode": mode, "default": default}
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"current: {mode or 'unknown'} ({default})")
    return 0


def cmd_verify(args) -> int:
    paths = hermes_paths(Path(args.hermes_dir) if args.hermes_dir else None)
    env = load_env_file(paths["env"])
    spec = get_spec(args.mode)
    api_key = resolve_var("${" + spec["api_key_env"] + "}", env)
    ok, err = verify_model(api_key, spec["base_url"], spec["verify_model"])
    if ok:
        print(f"✅ {spec['default']} verify OK")
        return 0
    print(f"❌ {spec['default']} verify failed: {err}")
    return 1


def cmd_backup_list(args) -> int:
    paths = hermes_paths(Path(args.hermes_dir) if args.hermes_dir else None)
    backups = list_backups(paths["backups"])
    if args.json:
        print(json.dumps(backups, ensure_ascii=False, indent=2))
    else:
        for item in backups:
            print(f"{item['backup_id']} source={item.get('source_default')} target={item.get('target_mode')} config={item.get('config_default')}")
    return 0


def cmd_rollback(args) -> int:
    paths = hermes_paths(Path(args.hermes_dir) if args.hermes_dir else None)
    with file_lock(paths["lock"]):
        restored = restore_backup(paths["config"], paths["backups"], args.backup_id)
    print(f"↩️ restored {args.backup_id} from {restored}")
    return 0


def cmd_switch(args) -> int:
    paths = hermes_paths(Path(args.hermes_dir) if args.hermes_dir else None)
    spec = get_spec(args.mode)
    env = load_env_file(paths["env"])
    api_key = resolve_var("${" + spec["api_key_env"] + "}", env)

    with file_lock(paths["lock"]):
        conf = _load_current_config(paths)
        source_default = _current_default(conf)
        preview = _update_config(load_yaml(paths["config"]), spec)

        print(f"📋 当前模型: {source_default} -> 将切换到: {spec['default']}")

        if args.dry_run:
            payload = {
                "action": "dry-run",
                "source_default": source_default,
                "target_mode": args.mode,
                "main_model": build_main_model_config(spec),
                "provider": build_provider_def(spec),
                "alias": dict([build_alias_update(spec)]),
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        ok, err = verify_model(api_key, spec["base_url"], spec["verify_model"])
        if not ok:
            return fail(f"❌ 目标模型验证失败: {err}")

        backup_id, _, _ = create_backup(paths["config"], paths["backups"], source_default, args.mode)
        save_yaml(paths["config"], preview)

        verify_conf = load_yaml(paths["config"])
        errors = _verify_written_config(verify_conf, spec)
        if errors:
            restore_backup(paths["config"], paths["backups"], backup_id)
            return fail("配置写入验证失败:\n- " + "\n- ".join(errors))

        if args.smoke_test:
            result = hermes_smoke_test()
            if result.returncode != 0 or "OK" not in (result.stdout + result.stderr):
                fallback = find_latest_valid_backup(paths["backups"], source_default, exclude_backup_id=backup_id)
                restore_id = fallback["backup_id"] if fallback else backup_id
                restore_backup(paths["config"], paths["backups"], restore_id)
                return fail(f"切换后 smoke test 失败，已回退到 {restore_id}\nstdout={result.stdout}\nstderr={result.stderr}")

    print(f"✅ switched to {spec['default']}")
    print(f"backup_id: {backup_id}")
    print(f"provider : {spec['provider_ref']}")
    print(f"api_key  : {mask('${' + spec['api_key_env'] + '}')}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hermes-model-switch")
    parser.add_argument("--hermes-dir", help="override ~/.hermes path")
    sub = parser.add_subparsers(dest="command", required=False)

    p_list = sub.add_parser("list", help="list supported models")
    p_list.add_argument("--json", action="store_true")
    p_list.set_defaults(func=cmd_list)

    p_current = sub.add_parser("current", help="show current model")
    p_current.add_argument("--json", action="store_true")
    p_current.set_defaults(func=cmd_current)

    p_verify = sub.add_parser("verify", help="verify a target model")
    p_verify.add_argument("mode", choices=[mode for mode, _ in iter_specs()])
    p_verify.set_defaults(func=cmd_verify)

    p_switch = sub.add_parser("switch", help="switch target model")
    p_switch.add_argument("mode", choices=[mode for mode, _ in iter_specs()])
    p_switch.add_argument("--dry-run", action="store_true")
    p_switch.add_argument("--smoke-test", action="store_true")
    p_switch.set_defaults(func=cmd_switch)

    p_backup = sub.add_parser("backup", help="backup operations")
    p_backup_sub = p_backup.add_subparsers(dest="backup_command", required=True)
    p_backup_list = p_backup_sub.add_parser("list", help="list backups")
    p_backup_list.add_argument("--json", action="store_true")
    p_backup_list.set_defaults(func=cmd_backup_list)

    p_rollback = sub.add_parser("rollback", help="restore a backup")
    p_rollback.add_argument("backup_id")
    p_rollback.set_defaults(func=cmd_rollback)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)

    legacy_modes = {mode for mode, _ in iter_specs()}
    if argv and argv[0] in legacy_modes:
        argv = ["switch", argv[0]] + argv[1:]
    if not argv:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
