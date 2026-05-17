# hermes-model-switch

Hermes Agent 模型切换工具，支持多模型一键切换，带预验证 + 自动回退。

## 功能特性

- **预验证切换**：切换前先 curl 验证目标模型是否可达，不可达不写配置
- **自动回退**：验证失败自动回退到上一个可用版本
- **model_aliases 同步**：切换时同步更新别名路由，避免请求走错 provider
- **配置二次验证**：写入后重新读回确认关键字段正确
- **备份机制**：每次切换自动备份，保留历史版本

## 安装

```bash
# 克隆仓库
git clone https://github.com/zhaotianxi/hermes-model-switch.git
cd hermes-model-switch

# 安装依赖
pip install ruamel.yaml

# 安装脚本到 ~/.hermes/bin/
mkdir -p ~/.hermes/bin
cp scripts/hermes_switch_model.py ~/.hermes/bin/
chmod +x ~/.hermes/bin/hermes_switch_model.py
```

## 配置架构

**`.env`**：存放敏感信息（API Key），**不提交到仓库**

**`~/.hermes/config.yaml`**：引用 `.env` 中的变量，格式如 `${VAR_NAME}`，安全且可提交

```
~/.hermes/
├── .env          # API Key 等敏感配置（不要提交）
└── config.yaml   # 主配置，引用 .env 中的变量
```

`.env` 示例：

```bash
# 替换为你自己的 API Key
MY_API_KEY=sk-your-key-here
```

## 快速使用

切换模型只需一条命令：

```bash
python3 ~/.hermes/bin/hermes_switch_model.py <标识>
```

支持的模型标识：

| 标识 | 说明 |
|------|------|
| `gpt` | GPT 系列模型 |
| `glm` | GLM 系列模型 |
| `minimax` | MiniMax 系列模型 |
| `ds` | DeepSeek 系列模型 |

示例：

```bash
python3 ~/.hermes/bin/hermes_switch_model.py gpt      # 切换到 GPT
python3 ~/.hermes/bin/hermes_switch_model.py glm      # 切换到 GLM
python3 ~/.hermes/bin/hermes_switch_model.py minimax  # 切换到 MiniMax
python3 ~/.hermes/bin/hermes_switch_model.py ds       # 切换到 DeepSeek
```

切换后**新会话生效**，当前会话不保证热切换。

## 添加自定义模型

如果你想添加其他模型，需要修改两个地方：

### 1. 编辑 `scripts/hermes_switch_model.py`

在 `TARGETS` 字典中添加新模型的配置：

```python
TARGETS = {
    # ... 现有模型 ...
    'my-model': {
        'default':     'my-model-name',          # 模型的实际名称
        'provider':    'custom:my-provider',      # provider 标识
        'base_url':   'https://api.example.com/v1',
        'api_key_env': 'MY_MODEL_API_KEY',        # 对应 .env 中的变量名
        'verify_model': 'my-model-name',          # 验证时用的模型名
        'alias_key':  'mymodel',                  # 别名路由的 key
    },
}
```

在 `PROVIDER_DEFS` 中添加 provider 定义：

```python
PROVIDER_DEFS = {
    # ... 现有 provider ...
    'my-model': {
        'name':     'my-provider',
        'base_url': 'https://api.example.com/v1',
        'api_key':  '${MY_MODEL_API_KEY}',         # 使用 .env 变量引用
        'model':    'my-model-name',
        'models':   {'my-model-name': {'context_length': 200000}},
    },
}
```

在 `ALIAS_UPDATES` 中添加别名更新映射：

```python
ALIAS_UPDATES = {
    # ... 现有映射 ...
    'my-model': {
        'mymodel': {
            'base_url': 'https://api.example.com/v1',
            'model':    'my-model-name',
            'provider': 'custom:my-provider',
        },
    },
}
```

### 2. 在 `~/.hermes/.env` 中添加 API Key

```bash
MY_MODEL_API_KEY=sk-your-key-here
```

### 3. 使用新模型

```bash
python3 ~/.hermes/bin/hermes_switch_model.py my-model
```

## 工作流程

```
┌─────────────────────────────────────────────┐
│  ~/.hermes/.env                             │
│  API_KEY=sk-xxx                             │
└──────────────┬──────────────────────────────┘
               │ ${API_KEY}
               ▼
┌─────────────────────────────────────────────┐
│  ~/.hermes/config.yaml                      │
│  api_key: ${API_KEY}   ← 变量引用，不暴露   │
│  base_url: https://api.example.com/v1        │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  hermes_switch_model.py                     │
│  1. 读取 .env → 解析变量                    │
│  2. curl 预验证模型可用性                   │
│  3. 可用 → 更新 config.yaml                 │
│  4. 失败 → 自动回退备份                     │
└─────────────────────────────────────────────┘
```

## 目录结构

```
hermes-model-switch/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── scripts/
│   └── hermes_switch_model.py   # 主切换脚本
├── skill/
│   ├── SKILL.md                  # Hermes 技能文档
│   └── references/
│       ├── quickstart.md         # 快速上手
│       └── bug5-backup-content-mismatch.md  # Bug 修复记录
└── tools/
    └── model-diagnosis.py        # API Key 诊断工具
```

## 发布新版本

```bash
# 1. 本地提交
git add . && git commit -m "描述本次变更"

# 2. 打 tag
git tag -a v1.1.0 -m "v1.1.0: 新增 xxx 功能"

# 3. 推送到 GitHub
git push && git push --tags
```

## License

MIT
