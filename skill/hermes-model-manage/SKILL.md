---
name: hermes-model-manage
description: 管理 hermes-model-switch 技能中的模型配置列表，支持增、删、改、查四项操作，以及 API Key 的修改。触发词：「加一个模型」「加个新模型」「新增模型」「添加模型」「删除模型」「删掉模型」「修改模型配置」「改一下模型」「换个模型」「查一下模型」「有哪些模型」「模型列表」「修改env」「更新env」「换个API Key」「API Key不对」
---

# hermes-model-manage

管理 hermes-model-switch 的模型配置，增删改查四项操作。

## 前置知识

### 脚本文件位置
```
~/.hermes/bin/hermes_switch_model.py
```

### 配置文件
```
~/.hermes/.env                    # API Key
~/.hermes/config.yaml            # 主配置（引用 .env 中的变量）
~/.hermes/backups/               # 自动备份
```

### 现有模型参考

| 标识 | provider | env 变量 |
|------|----------|----------|
| `gpt` | `custom:modelverse-gpt` | `MODELVERSE_API_KEY_GPT` |
| `glm` | `custom:svips-glm` | `SVIPS_API_KEY_GLM` |
| `minimax` | `custom:svips-minimax` | `SVIPS_API_KEY_MINIMAX` |
| `ds` | `custom:chudian-deepseek` | `CHUDIAN_API_KEY_DEEPSEEK` |

### 命名规范

新增模型时必须遵循以下命名规范：

**provider name**（用于 `custom:` 前缀）：
- 格式：`<平台>-<模型系列>`，全小写，中划线分隔
- 示例：`anthropic-claude`、`openai-gpt`、`zhipu-glm`、`deepseek-chat`

**env 变量名**：
- 格式：`<平台>_<模型标识>_API_KEY`，全大写，下划线分隔
- 示例：`ANTHROPIC_API_KEY_CLAUDE`、`OPENAI_API_KEY_GPT`

**alias key**（命令行标识）：
- 格式：简短好记的英文单词，全小写
- 示例：`claude`、`gpt`、`glm`、`ds`

## 四项操作

---

### 查：列出当前所有模型

直接读取脚本中的 `TARGETS` 字典，提取标识、default、base_url 信息。

```python
import re

with open('~/.hermes/bin/hermes_switch_model.py') as f:
    content = f.read()

# 提取 TARGETS
m = re.search(r'^TARGETS = \{(.*?)^\}', content, re.MULTILINE | re.DOTALL)
...
```

输出一张表，格式：

| 标识 | 模型名 | base_url | API Key 变量 |
|------|--------|----------|--------------|
| `gpt` | gpt-5.4 | https://api.modelverse.cn/v1 | `MODELVERSE_API_KEY_GPT` |
| ... | ... | ... | ... |

---

### 增：新增一个模型

**输入信息**：base_url、model_id、api_key，以及用户指定的标识（alias）

**步骤**：

**第一步**：生成规范命名

| 用户给的信息 | 生成规则 | 示例 |
|-------------|---------|------|
| base_url | 直接使用 | `https://api.anthropic.com/v1` |
| model_id | 直接使用 | `claude-sonnet-4` |
| api_key | 写入 `.env`，生成变量名 | `ANTHROPIC_API_KEY_CLAUDE` |
| alias | 用户指定或从 model_id 推断 | `claude` |
| provider name | 格式：`<平台>-<模型>` | `anthropic-claude` |

**第二步**：写入 `.env`

用 Python 字节替换：

```python
python3 -c "
import re
path = '/Users/xishuashua/.hermes/.env'
with open(path, 'rb') as f:
    content = f.read()
new_line = b'ANTHROPIC_API_KEY_CLAUDE=sk-ant-xxx\n'
if b'ANTHROPIC_API_KEY_CLAUDE' not in content:
    with open(path, 'wb') as f:
        f.write(content + new_line)
    print('Written')
else:
    print('Already exists')
"
```

**第三步**：修改脚本三处

在 `TARGETS` 中添加：

```python
'claude': {
    'default':     'claude-sonnet-4',
    'provider':    'custom:anthropic-claude',
    'base_url':   'https://api.anthropic.com/v1',
    'api_key_env': 'ANTHROPIC_API_KEY_CLAUDE',
    'verify_model': 'claude-sonnet-4',
    'alias_key':  'claude',
},
```

在 `PROVIDER_DEFS` 中添加：

```python
'claude': {
    'name':     'anthropic-claude',
    'base_url': 'https://api.anthropic.com/v1',
    'api_key':  '${ANTHROPIC_API_KEY_CLAUDE}',
    'model':    'claude-sonnet-4',
    'models':   {'claude-sonnet-4': {'context_length': 200000}},
},
```

在 `ALIAS_UPDATES` 中添加：

```python
'claude': {
    'claude': {
        'base_url': 'https://api.anthropic.com/v1',
        'model':    'claude-sonnet-4',
        'provider': 'custom:anthropic-claude',
    },
},
```

**第四步**：验证新增

```bash
python3 ~/.hermes/bin/hermes_switch_model.py <新标识>  # 应能成功切换
```

**第五步**：本地提交

```bash
git add . && git commit -m "feat: 新增 <模型名> 模型支持"
```

---

### 改：修改现有模型配置

**适用场景**：用户要求更换 API Key、修改 base_url、修改验证模型名等。

**步骤**：

**第一步**：确认要改的模型标识（如 `glm`、`minimax`）

**第二步**：找到需要改的字段，只改对应的值

| 要改的内容 | 改哪个字典 |
|-----------|-----------|
| 换 API Key | `.env` 中的变量 |
| 改 base_url | `TARGETS[mode]['base_url']` + `PROVIDER_DEFS[mode]['base_url']` + `ALIAS_UPDATES[mode][alias]['base_url']` |
| 改模型名 | `TARGETS[mode]['default']` + `PROVIDER_DEFS[mode]['model']` + `PROVIDER_DEFS[mode]['models'` 键 |
| 改验证模型 | `TARGETS[mode]['verify_model']` |
| 改 context_length | `PROVIDER_DEFS[mode]['models'][model_name]['context_length']` |

**第三步**：用 patch 精准替换，不要整段重写

```python
# 示例：修改 GLM 的 base_url
patch(old_string, new_string)
```

**第四步**：验证

```bash
python3 ~/.hermes/bin/hermes_switch_model.py <标识>  # 验证切换正常
```

**第五步**：本地提交

```bash
git add . && git commit -m "fix: 修改 <模型> 配置"
```

---

### 删：删除一个模型

**步骤**：

**第一步**：确认要删的模型标识

**第二步**：从 `TARGETS` 中删除对应条目

**第三步**：从 `PROVIDER_DEFS` 中删除对应条目

**第四步**：从 `ALIAS_UPDATES` 中删除对应条目

**第五步**：从 `.env` 中删除对应 API Key 变量（可选，建议保留以备不时之需）

**第六步**：本地提交

```bash
git add . && git commit -m "feat: 移除 <模型名> 模型支持"
```

## 操作原则

- **增改前先读脚本**，确认现有条目，避免覆盖
- **用 patch 精准替换**，不重写整个文件
- **增改后必须验证切换**，确认模型可正常调用
- **每次操作本地提交**，不直接 push 到远程
- **不要删除正在使用中的模型配置**，先确认当前不是该模型再删

## 常见问题

**Q: 用户给的 base_url 带尾部斜杠，怎么处理？**
A: 脚本内部用 `rstrip('/')` 处理，存储时保留原样即可。

**Q: 用户只给了一个新模型的信息，怎么起名字？**
A: 按命名规范推断：provider name 取平台域名+模型系列，alias 取简短英文名。

**Q: 删除模型后，当前正在使用这个模型会怎样？**
A: config.yaml 不会自动变更，只有下次切换时才会用到新列表。建议先切到其他模型再删除。
