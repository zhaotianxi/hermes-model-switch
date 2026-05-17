# Hermes Model Switch Quickstart

## 安装

```bash
git clone https://github.com/zhaotianxi/hermes-model-switch.git
cd hermes-model-switch
python3 -m pip install -e .
```

## 兼容脚本入口（可选）

```bash
mkdir -p ~/.hermes/bin
cp scripts/hermes_switch_model.py ~/.hermes/bin/
chmod +x ~/.hermes/bin/hermes_switch_model.py
```

## 最常用命令

```bash
# 看支持哪些模型
hermes-model-switch list

# 看当前模型
hermes-model-switch current

# 先预验证，不写配置
hermes-model-switch verify glm

# 先 dry-run，看将要改什么
hermes-model-switch switch glm --dry-run

# 真实切换
hermes-model-switch switch glm

# 切换后可选做 Hermes smoke test
hermes-model-switch switch gpt --smoke-test

# 查看备份
hermes-model-switch backup list
```

## 兼容旧命令

```bash
python3 ~/.hermes/bin/hermes_switch_model.py glm
```

## 当前备份格式

```text
~/.hermes/backups/<backup_id>/
  config.yaml
  meta.json
```

## 模型配置入口

模型定义统一维护在：

- `src/hermes_model_switch/model_specs.py`

其中 `MODEL_SPECS` 是单一事实源。

### 增删改查怎么做

- 查：`hermes-model-switch list` / `current`
- 增：在 `MODEL_SPECS` 中新增条目
- 改：修改对应模型条目
- 删：删除对应模型条目

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

### 示例文件

仓库已提供：

- `examples/config.yaml.example`
- `examples/.env.example`

示例 `.env` 片段：

```dotenv
MODELVERSE_API_KEY_GPT=sk-your-gpt-key
SVIPS_API_KEY_GLM=sk-your-glm-key
```

## 注意事项

1. 切换后建议开新会话生效
2. 当前实现会同步更新 `model`、`custom_providers`、`model_aliases`
3. 当前实现会加文件锁，避免并发写配置
4. OpenClaw 需单独处理
5. `.env` 仍需自行准备对应 API Key
