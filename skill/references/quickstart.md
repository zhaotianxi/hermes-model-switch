# Hermes Model Switch Quickstart

## 实际脚本位置

```
~/.hermes/bin/hermes_switch_model.py
```

技能目录下 `scripts/hermes_switch_model.py` 是备份，运行时使用 `~/.hermes/bin/` 下的版本。

## 快速切换命令

```bash
# 切换到 GLM-5.1
python3 ~/.hermes/bin/hermes_switch_model.py glm

# 切换到 MiniMax
python3 ~/.hermes/bin/hermes_switch_model.py minimax

# 切换到 GPT-5.4
python3 ~/.hermes/bin/hermes_switch_model.py gpt

# 切换到 DeepSeek (deepseek-v4-flash, 1000K上下文)
python3 ~/.hermes/bin/hermes_switch_model.py ds
```

## 四模型配置（已硬编码）

脚本内置，无需配置环境变量：

| 模型 | default | base_url | custom_providers name |
|------|---------|----------|----------------------|
| GLM-5.1 | GLM-5.1 | https://api.svips.org/v1 | SVIPS-GLM |
| MiniMax | MiniMax-M2.7-highspeed | https://api.svips.org/v1 | SVIPS |
| GPT-5.4 | gpt-5.4 | https://api.modelverse.cn/v1 | Api.modelverse.cn |
| DeepSeek | deepseek-v4-flash | https://llm.chudian.site/v1 | DeepSeek-ChuDian |

## 注意事项

1. 切换后**新会话生效**，当前会话不保证热切换
2. 脚本同时更新 `model:` 主配置 + `custom_providers:` 列表两处
3. `provider` 字段填 `custom`，不是 provider 名称
4. OpenClaw 需单独修改 `~/.openclaw/openclaw.json`
5. 每次切换自动备份到 `~/.hermes/backups/config.yaml.<model>.bak-<timestamp>`
6. DeepSeek 上下文长度 1000K tokens，其余模型 200K