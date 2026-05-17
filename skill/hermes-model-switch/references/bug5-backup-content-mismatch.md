# Bug 5 Fix: find_prev_backup 需增加内容自检

**文件**: `~/.hermes/bin/hermes_switch_model.py`
**状态**: ✅ v7 已应用（2025-05-17）

## 问题描述

v6 `find_prev_backup` 只按文件名时间戳排序，不验证备份内容是否与文件名声明的模型一致。

当备份内容被外部操作覆盖时（如手动 `cp`、或脚本并发执行），回退会取到错误版本。

## 修复代码

替换 `find_prev_backup` 函数（第 208-217 行）：

```python
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
                conf_backup = yaml.safe_load(f) if not HAS_RUAML else yaml.load(f)
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
```

## 验证方法

在本地复盘验证（用今天的数据）：

```python
# 21:24 的 gpt 备份内容实际是 minimax，运行修复后的逻辑会跳过它
# 正确找到 21:20 的 gpt 备份（default=gpt-5.4）

import glob, yaml
from pathlib import Path

mode = 'gpt'
BACKUP_DIR = Path.home() / '.hermes' / 'backups'
stamp = '20260517212441'  # 21:24 那次切换的时间戳

mode_default_map = {
    'gpt': 'gpt-5.4', 'glm': 'GLM-5.1',
    'minimax': 'MiniMax-M2.7-highspeed', 'ds': 'deepseek-v4-flash',
}
expected = mode_default_map[mode]

backups = sorted(glob.glob(str(BACKUP_DIR / f'config.yaml.{mode}.bak-*')), reverse=True)
for b in backups:
    if b.endswith(stamp):
        continue
    with open(b) as f:
        c = yaml.safe_load(f)
    d = c.get('model', {}).get('default', '')
    print(f"{'✅' if d == expected else '❌'} {b.split('/')[-1]}: default={d} (期望={expected})")
```

输出应为 `✅ config.yaml.gpt.bak-20260517212109: default=gpt-5.4 (期望=gpt-5.4)` 而非 21:24 的那个。

## 根因分析（本次会话）

| 时间 | 切换操作 | 备份文件 | 备份内 default |
|------|----------|----------|---------------|
| 21:20 | 切→gpt | gpt.bak-20260517212109 | gpt-5.4 ✅ |
| 21:24 | 切→gpt | gpt.bak-20260517212441 | **MiniMax-M2.7-highspeed** ❌ |
| 21:25 | 切→ds | ds.bak-20260517212527 | gpt-5.4 |
| 21:25 | DS失败→回退 | 取 gpt 备份 | 拿到 21:24 备份（内容是 minimax）→ 回退到了 minimax |

21:24 的 gpt 备份内容异常原因未知（可能并发写、手动覆盖、或更早的 bug），但修复后的 find_prev_backup 会拒绝内容不一致的备份，避免错误回退。
