---
name: hermes-model-switch
description: 管理 Hermes Agent 大模型配置，支持切换模型和增删改查。当用户说「切到GPT/MiniMax/GLM/DeepSeek」时执行切换；当用户说「加模型/删模型/改模型/查模型列表/修改API Key」时执行配置管理。先验证连通性再操作，失败不写配置，自动回退。
---

# hermes-model-switch

管理 Hermes Agent 大模型配置，支持**切换**和**增删改查**两大操作。

---

## 一、切换模型

### 切换流程（必须按顺序执行）

**第一步：连通性验证** → **第二步：写入配置** → **第三步：二次验证**。验证失败不写配置，保持现状。

### 第一步：验证目标模型可达

用 curl 单独测每个模型，确认返回含 `"choices"` 字段：

```bash
# GPT-5.4 (modelverse.cn)
curl -s https://api.modelverse.cn/v1/chat/completions \
  -H "Authorization: Bearer $MODELVERSE_API_KEY_GPT" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-5.4","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'

# GLM-5.1 (svips.org)
curl -s https://api.svips.org/v1/chat/completions \
  -H "Authorization: Bearer $SVIPS_API_KEY_GLM" \
  -H "Content-Type: application/json" \
  -d '{"model":"GLM-5.1","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'

# MiniMax (svips.org)
curl -s https://api.svips.org/v1/chat/completions \
  -H "Authorization: Bearer $SVIPS_API_KEY_MINIMAX" \
  -H "Content-Type: application/json" \
  -d '{"model":"MiniMax-M2.7-highspeed","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'

# DeepSeek (chudian.site)
curl -s https://llm.chudian.site/v1/chat/completions \
  -H "Authorization: Bearer $CHUDIAN_API_KEY_DEEPSEEK" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
```

返回含 `"choices":` 即为验证通过。返回 `503`/`401`/`ModelNotOpen` 等均为验证失败。

### 第二步：验证通过后，写入配置

调用脚本，脚本内部会再次验证并备份：

```bash
python3 ~/.hermes/bin/hermes_switch_model.py gpt      # GPT-5.4
python3 ~/.hermes/bin/hermes_switch_model.py glm      # GLM-5.1
python3 ~/.hermes/bin/hermes_switch_model.py minimax  # MiniMax-M2.7-highspeed
python3 ~/.hermes/bin/hermes_switch_model.py ds       # deepseek-v4-flash
```

脚本验证失败时**不会写入任何配置**，直接退出并报错。

### 第三步：验证切换结果

```bash
hermes chat -q "只回复 OK" -Q
```

**验证失败处理**：脚本已支持自动回退，无需手动处理。

## 各模型配置参考

| 标识 | default | base_url | provider | env 变量 |
|------|---------|----------|----------|----------|
| `gpt` | `gpt-5.4` | `https://api.modelverse.cn/v1` | `custom:modelverse-gpt` | `MODELVERSE_API_KEY_GPT` |
| `glm` | `GLM-5.1` | `https://api.svips.org/v1` | `custom:svips-glm` | `SVIPS_API_KEY_GLM` |
| `minimax` | `MiniMax-M2.7-highspeed` | `https://api.svips.org/v1` | `custom:svips-minimax` | `SVIPS_API_KEY_MINIMAX` |
| `ds` | `deepseek-v4-flash` | `https://llm.chudian.site/v1` | `custom:chudian-deepseek` | `CHUDIAN_API_KEY_DEEPSEEK` |

## 关键约束

- **第一步验证失败，不写配置，保持现状**
- **验证失败自动回退到上一个可用版本**
- API Key 从 `~/.hermes/.env` 读取，配置中必须用 `${VAR_NAME}` 引用语法
- 切换后 `model_aliases` 路由自动生效，新会话立即命中正确模型
- OpenClaw 需单独切换，不自动同步

## 切换常见错误

- `503 上游服务调用失败`：服务商临时不可用，等待后重试验证
- `401`：API Key 失效，需从 `.env` 重新配置
- `ModelNotOpen`：模型未开通或名称错误，确认 `verify_model` 字段正确
- 切换后仍跑原模型：新会话生效，或检查 `model_aliases` 路由是否命中

---

## 二、增删改查

### 前置知识

**脚本文件位置**：`~/.hermes/bin/hermes_switch_model.py`

**配置文件**：
```
~/.hermes/.env          # API Key 等敏感配置
~/.hermes/config.yaml  # 主配置（引用 .env 中的变量）
~/.hermes/backups/     # 自动备份
```

### 命名规范

新增模型时必须遵循以下规范：

| 命名项 | 格式 | 示例 |
|--------|------|------|
| provider name | `<平台>-<模型系列>` 全小写，中划线 | `anthropic-claude` |
| env 变量 | `<平台>_<标识>_API_KEY` 全大写，下划线 | `ANTHROPIC_API_KEY_CLAUDE` |
| alias | 简短英文小写 | `claude` |

---

### 查：列出当前所有模型

直接读取脚本中的 `TARGETS` 字典，提取标识、default、base_url 信息，输出格式化表格。

---

### 增：新增一个模型

用户提供 base_url、model_id、api_key，以及标识（alias）。

**步骤**：

1. **生成命名**（遵循命名规范）
2. **写入 `.env`**：用 Python 字节追加，不覆盖已有内容
3. **修改脚本三处**：`TARGETS` + `PROVIDER_DEFS` + `ALIAS_UPDATES`
4. **验证**：`python3 ~/.hermes/bin/hermes_switch_model.py <标识>`
5. **本地提交**

示例交互：

> 用户：「给我加一个 Claude 模型，baseurl 是 `https://api.anthropic.com/v1`，modelid 是 `claude-sonnet-4`，apikey 是 `sk-ant-xxx`」
>
> 我：「好，我来按规范添加。provider 命名为 `anthropic-claude`，变量名 `ANTHROPIC_API_KEY_CLAUDE`，alias `claude`。开始写入配置...」

---

### 改：修改现有模型配置

| 要改的内容 | 改哪个位置 |
|-----------|-----------|
| 换 API Key | `~/.hermes/.env` 中的变量值 |
| 改 base_url | `TARGETS[mode]['base_url']` + `PROVIDER_DEFS[mode]['base_url']` + `ALIAS_UPDATES[mode][alias]['base_url']` |
| 改模型名 | `TARGETS[mode]['default']` + `PROVIDER_DEFS[mode]['model']` + `PROVIDER_DEFS[mode]['models'` 键 |
| 改验证模型 | `TARGETS[mode]['verify_model']` |
| 改 context_length | `PROVIDER_DEFS[mode]['models'][model_name]['context_length']` |

用 patch 精准替换，只改对应的值，不重写整段代码。

示例交互：

> 用户：「把 GLM 的验证模型改成 `glm-4-plus`」
>
> 我：「好，只改 `TARGETS['glm']['verify_model']` 这一处，其他不动。开始修改...」

> 用户：「换个 API Key，MiniMax 的 key 换成 `sk-new-key-xxx`」
>
> 我：「好，修改 `.env` 中 `SVIPS_API_KEY_MINIMAX` 的值。开始写入...」

---

### 删：删除一个模型

从 `TARGETS`、`PROVIDER_DEFS`、`ALIAS_UPDATES` 三处删除对应条目。`.env` 中的 key 建议保留以备不时之需。

示例交互：

> 用户：「把 DeepSeek 从切换列表里删掉」
>
> 我：「好的，删除标识 `ds` 相关配置，`.env` 中的 key 保留。开始修改...」

---

## 操作原则

- **增改前先读脚本**，确认现有条目，避免覆盖
- **用 patch 精准替换**，不重写整个文件
- **增改后必须验证切换**，确认模型可正常调用
- **每次操作本地提交**，不直接 push 到远程
- **不要删除正在使用中的模型配置**，先确认当前不是该模型再删

---

## 陷阱：.env 中 API Key 验证

**症状**：更新 `.env` 中的 API Key 后，用 `grep` / `print()` / `echo` 查看到的值始终是 `***`，疑似未更新成功。

**原因**：工具层对敏感信息有自动脱敏机制，输出时将 `sk-` 开头的字符串替换为 `***`，但文件实际内容并未改变。

**验证方法**：用 Python 字节级读取，绕过输出掩码：

```python
with open('/Users/xishuashua/.hermes/.env', 'rb') as f:
    content = f.read()
idx = content.find(b'SVIPS_API_KEY_GLM')
print(content[idx:idx+80].decode('utf-8', errors='replace'))
```

**不靠谱的方法**：`grep ~/.hermes/.env`、`print()`、`echo $VAR` — 都会被脱敏。

---

## v6/v7 修复清单（历史积累）

- **Bug 1（v6）**：model_aliases 未同步 → 增加 `ALIAS_UPDATES` 映射
- **Bug 2（v6）**：custom_providers 中 api_key 错误 → 写入后二次验证
- **Bug 3（v6）**：yaml.safe_dump 丢失注释 → 优先用 ruamel.yaml
- **Bug 4（v6）**：回退逻辑用 mtime 排序 → 改用文件名时间戳排序
- **Bug 5（v7）**：find_prev_backup 内容自检 → 验证备份内容与文件名一致
- **Bug 6（v7）**：备份文件名用目标模型而非源模型 → 改用 `prev_mode` 命名
