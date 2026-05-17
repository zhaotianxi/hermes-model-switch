#!/usr/bin/env python3
"""
Hermes 模型切换脚本 v6（带预验证 + 自动回退 + model_aliases 同步）

v6 修复：
  1. 切换时同步更新 model_aliases 中对应模型的 provider 和 base_url
  2. 用 ruamel.yaml 替代 yaml.safe_dump，保留注释和格式
  3. 回退逻辑优先用文件名时间戳排序，而非 mtime
  4. 写入后二次验证：重新读回 config.yaml 确认 key 字段正确

支持: gpt, glm, minimax, ds(DeepSeek)
切换前先验证模型可用性，只切换验证通过的模型。
验证失败时自动回退到上一个可用版本。
"""
import sys, shutil, os, json, subprocess, glob, re
from datetime import datetime
from pathlib import Path

try:
    from ruamel.yaml import YAML
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    HAS_RUAML = True
except ImportError:
    try:
        import yaml as _yaml
        yaml = None
        HAS_RUAML = False
    except ImportError:
        print("缺少 YAML 库，请安装: python3 -m pip install ruamel.yaml", file=sys.stderr)
        sys.exit(2)

CONFIG = Path.home() / '.hermes' / 'config.yaml'
BACKUP_DIR = Path.home() / '.hermes' / 'backups'
ENV_FILE  = Path.home() / '.hermes' / '.env'

# 从 .env 加载真实 key（变量引用 → 真实值）
def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, _, v = line.partition('=')
            env[k.strip()] = v.strip()
    return env

def resolve_var(s, env):
    """把 ${VAR_NAME} 替换为 env 中的真实值"""
    if not isinstance(s, str):
        return s
    while True:
        m = re.search(r'\$\{([^}]+)\}', s)
        if not m:
            break
        s = s.replace(m.group(0), env.get(m.group(1), ''))
    return s

# 各模型配置
TARGETS = {
    'gpt': {
        'default': 'gpt-5.4',
        'provider': 'custom:modelverse-gpt',
        'base_url': 'https://api.modelverse.cn/v1',
        'api_key_env': 'MODELVERSE_API_KEY_GPT',
        'verify_model': 'gpt-5.4',
        'alias_key': 'gpt',
    },
    'glm': {
        'default': 'GLM-5.1',
        'provider': 'custom:svips-glm',
        'base_url': 'https://api.svips.org/v1',
        'api_key_env': 'SVIPS_API_KEY_GLM',
        'verify_model': 'GLM-5.1',
        'alias_key': 'glm',
    },
    'minimax': {
        'default': 'MiniMax-M2.7-highspeed',
        'provider': 'custom:svips-minimax',
        'base_url': 'https://api.svips.org/v1',
        'api_key_env': 'SVIPS_API_KEY_MINIMAX',
        'verify_model': 'MiniMax-M2.7-highspeed',
        'alias_key': 'minimax',
    },
    'ds': {
        'default': 'deepseek-v4-flash',
        'provider': 'custom:chudian-deepseek',
        'base_url': 'https://llm.chudian.site/v1',
        'api_key_env': 'CHUDIAN_API_KEY_DEEPSEEK',
        'verify_model': 'deepseek-v4-flash',
        'alias_key': 'deepseek',
    },
}

PROVIDER_DEFS = {
    'gpt': {
        'name': 'modelverse-gpt',
        'base_url': 'https://api.modelverse.cn/v1',
        'api_key': '${MODELVERSE_API_KEY_GPT}',
        'model': 'gpt-5.4',
        'models': {'gpt-5.4': {'context_length': 200000}},
    },
    'glm': {
        'name': 'svips-glm',
        'base_url': 'https://api.svips.org/v1',
        'api_key': '${SVIPS_API_KEY_GLM}',
        'model': 'GLM-5.1',
        'models': {'GLM-5.1': {'context_length': 200000, 'max_output_tokens': 200000}},
    },
    'minimax': {
        'name': 'svips-minimax',
        'base_url': 'https://api.svips.org/v1',
        'api_key': '${SVIPS_API_KEY_MINIMAX}',
        'model': 'MiniMax-M2.7-highspeed',
        'models': {'MiniMax-M2.7-highspeed': {'context_length': 200000}},
    },
    'ds': {
        'name': 'chudian-deepseek',
        'base_url': 'https://llm.chudian.site/v1',
        'api_key': '${CHUDIAN_API_KEY_DEEPSEEK}',
        'model': 'deepseek-v4-flash',
        'models': {'deepseek-v4-flash': {'context_length': 1000000, 'max_output_tokens': 1000}},
    },
}

# model_aliases 更新映射：切换到某模型时，需要更新哪些 alias
ALIAS_UPDATES = {
    'gpt': {
        'gpt': {'base_url': 'https://api.modelverse.cn/v1', 'model': 'gpt-5.4', 'provider': 'custom:modelverse-gpt'},
    },
    'glm': {
        'glm': {'base_url': 'https://api.svips.org/v1', 'model': 'GLM-5.1', 'provider': 'custom:svips-glm'},
    },
    'minimax': {
        'minimax': {'base_url': 'https://api.svips.org/v1', 'model': 'MiniMax-M2.7-highspeed', 'provider': 'custom:svips-minimax'},
    },
    'ds': {
        'deepseek': {'base_url': 'https://llm.chudian.site/v1', 'model': 'deepseek-v4-flash', 'provider': 'custom:chudian-deepseek'},
    },
}


def verify_model(key, base_url, model_name, timeout=12):
    """用 curl 测试模型是否可用，返回 (成功bool, 错误信息)"""
    chat_url = base_url.rstrip('/') + '/chat/completions'
    payload = json.dumps({
        "model": model_name,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 5
    })
    try:
        r = subprocess.run(
            ["curl", "-s", chat_url,
             "-H", f"Authorization: Bearer {key}",
             "-H", "Content-Type: application/json",
             "-d", payload,
             "--max-time", str(timeout)],
            capture_output=True, text=True, timeout=timeout + 5
        )
        j = json.loads(r.stdout.strip())
        err = j.get("error", {})
        code = err.get("code", "")
        if code in ("ModelNotOpen", "NotFound") or j.get("object") == "error":
            return False, f"未激活或不存在 (code={code})"
        if j.get("choices"):
            return True, ""
        return False, str(err.get("message", ""))[:60]
    except subprocess.TimeoutExpired:
        return False, "请求超时"
    except Exception as e:
        return False, str(e)[:60]


def mask(v):
    if not v:
        return '(empty)'
    return v[:6] + '...' + v[-4:] if len(v) > 8 else '***'


def fail(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def load_config():
    """加载 config.yaml，优先用 ruamel.yaml 保留格式"""
    if HAS_RUAML:
        with open(CONFIG, 'r', encoding='utf-8') as f:
            return yaml.load(f)
    else:
        import yaml as _yaml
        with open(CONFIG, 'r', encoding='utf-8') as f:
            return _yaml.safe_load(f) or {}


def save_config(conf):
    """保存 config.yaml，优先用 ruamel.yaml 保留格式"""
    if HAS_RUAML:
        with open(CONFIG, 'w', encoding='utf-8') as f:
            yaml.dump(conf, f)
    else:
        import yaml as _yaml
        CONFIG.write_text(_yaml.safe_dump(conf, allow_unicode=True, sort_keys=False), encoding='utf-8')


def find_prev_backup(mode, current_stamp):
    """找到目标模型对应备份中第二新的（排除本次生成的）

    v7 修复：回退前验证备份内容中的 model.default 是否与文件名声明一致，
    避免因备份内容与文件名不匹配导致回退到错误模型。
    """
    # 声明 → default 映射
    mode_default_map = {
        'gpt':      'gpt-5.4',
        'glm':      'GLM-5.1',
        'minimax':  'MiniMax-M2.7-highspeed',
        'ds':       'deepseek-v4-flash',
    }
    expected_default = mode_default_map.get(mode, '')

    pattern = str(BACKUP_DIR / f'config.yaml.{mode}.bak-*')
    backups = sorted(glob.glob(pattern), reverse=True)

    for b in backups:
        if b.endswith(current_stamp):
            continue
        try:
            with open(b, 'r', encoding='utf-8') as f:
                if HAS_RUAML:
                    conf_backup = yaml.load(f)
                else:
                    import yaml as _yaml
                    conf_backup = _yaml.safe_load(f)
            backup_default = conf_backup.get('model', {}).get('default', '')
            if hasattr(backup_default, 'value'):
                backup_default = backup_default.value
            if backup_default == expected_default:
                return b
        except Exception:
            continue

    # fallback：保留原行为
    for b in backups:
        if not b.endswith(current_stamp):
            return b
    return backups[0] if backups else None


def restore_backup(backup_path):
    """验证失败时还原备份"""
    if backup_path and os.path.exists(backup_path):
        shutil.copy2(backup_path, CONFIG)
        print(f'↩️  已还原备份: {backup_path}', file=sys.stderr)
    else:
        print(f'⚠️  未找到可用备份，配置未改变', file=sys.stderr)


if len(sys.argv) < 2 or sys.argv[1] not in TARGETS:
    fail('用法: python3 hermes_switch_model.py <gpt|glm|minimax|ds> [--no-restore]')

mode = sys.argv[1]
if not CONFIG.exists():
    fail('配置文件不存在: ' + str(CONFIG))

env = load_env()
spec = TARGETS[mode]

# ── 0. 读取当前配置，记录原模型（用于回退） ─────────────────
conf = load_config()
if HAS_RUAML:
    prev_default = conf.get('model', {}).get('default', 'unknown')
    if hasattr(prev_default, 'value'):
        prev_default = prev_default.value
else:
    prev_default = conf.get('model', {}).get('default', 'unknown')
print(f'📋 当前模型: {prev_default} → 将切换到: {spec["default"]}')

# ── 1. 备份当前配置（文件名用源模型，而非目标模型）────────
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime('%Y%m%d%H%M%S')
prev_mode_map = {'gpt-5.4':'gpt', 'GLM-5.1':'glm', 'MiniMax-M2.7-highspeed':'minimax', 'deepseek-v4-flash':'ds'}
backup_mode = prev_mode_map.get(prev_default, mode)  # 用源模型名做备份文件名
backup = BACKUP_DIR / ('config.yaml.' + backup_mode + '.bak-' + stamp)
shutil.copy2(CONFIG, backup)
print(f'📦 已备份当前配置: {backup}')

# ── 2. 预验证（curl 测试目标模型可用性）───────────────────
real_key = resolve_var('${' + spec['api_key_env'] + '}', env)
if not real_key:
    fail(f'❌ 找不到 API Key: {spec["api_key_env"]}，请检查 ~/.hermes/.env')

print(f'🔄 正在验证 {spec["default"]} ...')
ok, err = verify_model(real_key, spec['base_url'], spec['verify_model'])
if not ok:
    print(f'❌ {spec["default"]} 验证失败: {err}', file=sys.stderr)
    prev_mode_map = {'gpt-5.4':'gpt', 'GLM-5.1':'glm', 'MiniMax-M2.7-highspeed':'minimax', 'deepseek-v4-flash':'ds'}
    prev_mode = prev_mode_map.get(prev_default, None)
    if prev_mode and prev_mode != mode:
        prev_backup = find_prev_backup(prev_mode, stamp)
        print(f'🔄 回退到上一个可用版本({prev_default}) ...', file=sys.stderr)
        restore_backup(prev_backup)
    else:
        print(f'🔄 还原到切换前配置 ...', file=sys.stderr)
        restore_backup(backup)
    fail(f'↩️  已还原（{spec["default"]} 不可用）')
print(f'✅ {spec["default"]} 验证通过')

# ── 3. 读取并更新配置 ──────────────────────────────────────
conf = load_config()
conf.setdefault('model', {})
conf.setdefault('custom_providers', [])

prov_def = PROVIDER_DEFS[mode]

# 更新 model 主配置
conf['model']['default']  = spec['default']
conf['model']['provider'] = spec['provider']
conf['model']['base_url'] = spec['base_url']
conf['model']['api_key']  = '${' + spec['api_key_env'] + '}'

# 更新 custom_providers
cp_list = conf['custom_providers']
found = False
for i, entry in enumerate(cp_list):
    entry_name = entry.get('name', '')
    if hasattr(entry_name, 'value'):
        entry_name = entry_name.value
    if entry_name == prov_def['name']:
        cp_list[i] = {
            'name': prov_def['name'],
            'base_url': prov_def['base_url'],
            'api_key': prov_def['api_key'],
            'model': prov_def['model'],
            'models': prov_def['models'],
        }
        found = True
        break
if not found:
    cp_list.append({
        'name': prov_def['name'],
        'base_url': prov_def['base_url'],
        'api_key': prov_def['api_key'],
        'model': prov_def['model'],
        'models': prov_def['models'],
    })

conf['custom_providers'] = cp_list

# ── 4. 同步更新 model_aliases ──────────────────────────────
# 修复 Bug：切换模型时必须同步更新 model_aliases 中对应的 provider 引用
aliases = conf.get('model_aliases')
if aliases is None:
    aliases = {}
    conf['model_aliases'] = aliases

alias_updates = ALIAS_UPDATES.get(mode, {})
for alias_key, alias_val in alias_updates.items():
    if alias_key not in aliases:
        aliases[alias_key] = {}
    target = aliases[alias_key]
    # ruamel.yaml 的 CommentedMap 需要逐字段更新
    for k, v in alias_val.items():
        target[k] = v
    # 确保 api_key 也正确设置
    prov_name = alias_val['provider'].replace('custom:', '')
    for prov in cp_list:
        pn = prov.get('name', '')
        if hasattr(pn, 'value'):
            pn = pn.value
        if pn == prov_name:
            target['api_key'] = prov.get('api_key', '')
            break

print(f'✅ 已同步 model_aliases: {list(alias_updates.keys())}')

# ── 5. 写入 ────────────────────────────────────────────────
save_config(conf)

# ── 6. 二次验证：重新读回配置确认关键字段正确 ──────────────
verify_conf = load_config()
v_default = verify_conf.get('model', {}).get('default', '')
if hasattr(v_default, 'value'):
    v_default = v_default.value
v_provider = verify_conf.get('model', {}).get('provider', '')
if hasattr(v_provider, 'value'):
    v_provider = v_provider.value
v_api_key = verify_conf.get('model', {}).get('api_key', '')
if hasattr(v_api_key, 'value'):
    v_api_key = v_api_key.value

errors = []
if v_default != spec['default']:
    errors.append(f'default 不匹配: 写入={spec["default"]}, 读回={v_default}')
if v_provider != spec['provider']:
    errors.append(f'provider 不匹配: 写入={spec["provider"]}, 读回={v_provider}')
expected_key = '${' + spec['api_key_env'] + '}'
if v_api_key != expected_key:
    errors.append(f'api_key 不匹配: 写入={expected_key}, 读回={v_api_key}')

# 验证 custom_providers 中目标 provider 的 api_key
v_providers = verify_conf.get('custom_providers', [])
for p in v_providers:
    pn = p.get('name', '')
    if hasattr(pn, 'value'):
        pn = pn.value
    if pn == prov_def['name']:
        pk = p.get('api_key', '')
        if hasattr(pk, 'value'):
            pk = pk.value
        if pk != prov_def['api_key']:
            errors.append(f'custom_providers.{pn}.api_key 不匹配: 写入={prov_def["api_key"]}, 读回={pk}')

# 验证 model_aliases 中对应 alias 的 provider
v_aliases = verify_conf.get('model_aliases', {})
for alias_key, alias_val in alias_updates.items():
    if alias_key in v_aliases:
        v_alias_prov = v_aliases[alias_key].get('provider', '')
        if hasattr(v_alias_prov, 'value'):
            v_alias_prov = v_alias_prov.value
        if v_alias_prov != alias_val['provider']:
            errors.append(f'model_aliases.{alias_key}.provider 不匹配: 写入={alias_val["provider"]}, 读回={v_alias_prov}')

if errors:
    print('⚠️  配置写入验证发现问题:', file=sys.stderr)
    for e in errors:
        print(f'  - {e}', file=sys.stderr)
    print('🔄 正在还原备份 ...', file=sys.stderr)
    restore_backup(backup)
    fail(f'↩️  配置写入验证失败，已还原备份')
else:
    print('✅ 配置写入验证通过')

print()
print(f'✅ 已切换到: {spec["default"]}')
print(f'   切换前备份: {backup}')
print(f'   default : {spec["default"]}')
print(f'   provider: {spec["provider"]}')
print(f'   base_url: {spec["base_url"]}')
print(f'   api_key : {mask(expected_key)}')
print()
print('⚠️  新会话/新轮次生效最稳。OpenClaw 需单独切换。')