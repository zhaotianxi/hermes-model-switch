---
name: hermes-model-switch
description: |
  管理和切换 Hermes Agent 的大模型配置。支持：
  - 切换模型（GPT / GLM / MiniMax / DeepSeek），预验证 + dry-run + 备份 + 二次验证 + 可选 smoke test
  - 查看当前模型 / 列出模型 / 验证模型 / 列出备份 / 回退备份
  - 兼容旧入口：python3 ~/.hermes/bin/hermes_switch_model.py <mode>
  触发词：切换、gpt、glm、minimax、ds、deepseek、dry-run、查模型、当前模型、回退备份、查看备份
---

# hermes-model-switch

## 对外版本

当前对外版本按 semver 管理，现行为 **1.1.0**。历史文档里的 v6 / v7 是修复阶段编号，不再作为主版本号。

## 核心命令

### 列出支持模型

```bash
hermes-model-switch list
```

### 查看当前模型

```bash
hermes-model-switch current
```

### 预验证目标模型

```bash
hermes-model-switch verify gpt
hermes-model-switch verify glm
hermes-model-switch verify minimax
hermes-model-switch verify ds
```

### dry-run

```bash
hermes-model-switch switch glm --dry-run
```

### 执行切换

```bash
hermes-model-switch switch gpt
hermes-model-switch switch glm
hermes-model-switch switch minimax
hermes-model-switch switch ds
```

### 切换后做 Hermes smoke test

```bash
hermes-model-switch switch gpt --smoke-test
```

### 查看备份

```bash
hermes-model-switch backup list
```

### 回退备份

```bash
hermes-model-switch rollback <backup_id>
```

## 兼容旧入口

```bash
python3 ~/.hermes/bin/hermes_switch_model.py gpt
```

等价于：

```bash
hermes-model-switch switch gpt
```

## 当前实现要点

1. 切换前验证目标模型可达
2. 写入前获取文件锁，避免并发写 `config.yaml`
3. 切换时同步更新三处：
   - `model`
   - `custom_providers`
   - `model_aliases`
4. 切换前创建目录式备份：
   - `~/.hermes/backups/<backup_id>/config.yaml`
   - `~/.hermes/backups/<backup_id>/meta.json`
5. 写入后读回校验关键字段
6. 开启 `--smoke-test` 时，额外执行：
   - `hermes chat -q "只回复 OK" -Q`
7. smoke test 失败自动回退

## 模型配置管理（增删改查）

当前实现把模型定义统一收敛到：

- `src/hermes_model_switch/model_specs.py`

其中核心对象是 `MODEL_SPECS`。模型配置的单一事实源就在这里。

### 查

- 用户侧：`hermes-model-switch list`、`hermes-model-switch current`
- 代码侧：`iter_specs()`、`get_spec(mode)`、`mode_from_default(default_model)`

### 增

新增模型时，直接在 `MODEL_SPECS` 中新增一个条目。

### 改

修改模型时，直接调整 `MODEL_SPECS` 中对应条目。

CLI 会通过以下函数自动派生最终写入配置：

- `build_main_model_config(spec)`
- `build_provider_def(spec)`
- `build_alias_update(spec)`

### 删

删除模型时，直接从 `MODEL_SPECS` 中删除对应条目。

> 注意：当前实现的“删”不会自动清理用户现有 `config.yaml` 里旧的 `custom_providers` 或 `model_aliases` 残留项。

## 示例

### 新增模型示例（qwen）

```python
"qwen": {
    "label": "Qwen-Plus",
    "default": "qwen-plus",
    "provider_name": "aliyun-qwen",
    "provider_ref": "custom:aliyun-qwen",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_key_env": "DASHSCOPE_API_KEY_QWEN",
    "verify_model": "qwen-plus",
    "alias": "qwen",
    "models": {
        "qwen-plus": {
            "context_length": 128000
        }
    },
},
```

加完后，`list / verify / switch` 会自动支持该模型。

### config.yaml 示例片段

```yaml
model:
  default: gpt-5.4
  provider: custom:modelverse-gpt
  base_url: https://api.modelverse.cn/v1
  api_key: ${MODELVERSE_API_KEY_GPT}
```

### .env 示例片段

```dotenv
MODELVERSE_API_KEY_GPT=sk-your-gpt-key
SVIPS_API_KEY_GLM=sk-your-glm-key
```

## 备份结构

```text
~/.hermes/backups/
  20260517T132500Z-gpt/
    config.yaml
    meta.json
```

`meta.json` 记录：
- `backup_id`
- `created_at`
- `source_default`
- `source_mode`
- `target_mode`

## 模型定义来源

当前实现不再维护三份重复配置，而是统一由 `src/hermes_model_switch/model_specs.py` 中的 `MODEL_SPECS` 作为单一事实源，再派生：

- 主配置 `model`
- `custom_providers`
- `model_aliases`

## 项目边界

- 不自动切 OpenClaw
- 不创建 API Key
- 不保证当前会话热切换
- 不处理 `.env` 加密
