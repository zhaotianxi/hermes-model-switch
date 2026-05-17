---
name: hermes-model-switch
description: |
  管理和切换 Hermes Agent 的大模型配置。支持：
  - 切换模型（GPT / GLM / MiniMax / DeepSeek），预验证+自动回退+二次验证
  - 配置增删改查（添加新模型 / 删除模型 / 修改配置 / 列出当前模型）
  - 修改 API Key（精准替换 .env 中指定模型的 key）
  触发词：切换、gpt、glm、minimax、ds、deepseek、加模型、删模型、改模型、改key、查模型、查看模型列表
---

# hermes-model-switch

模型切换 + 配置管理统一技能。

## 工作原理

```
用户触发切换
     │
     ▼
第一步：curl 预验证模型可达性
     │
  ┌──┴──┐
  │     │
失败   通过
  │     │
  │     ▼
  │ 第二步：备份配置 → 更新 config.yaml（三处同步）
  │     │
  │     ▼
  │ 第三步：二次验证关键字段
  │     │
  │  ┌──┴──┐
  │  │     │
  │失败  通过
  │  │     │
  │  ▼     ▼
  │回退   完成，新会话生效
  ▼
  还原备份，报错退出
```

## 切换操作

### 预验证（第一步）

用 curl 测试目标模型是否可达，返回含 `"choices"` 即为通过：

```bash
curl -s https://api.svips.org/v1/chat/completions \
  -H "Authorization: Bearer ${SVIPS_API_KEY_MINIMAX}" \
  -H "Content-Type: application/json" \
  -d '{"model":"MiniMax-M2.7-highspeed","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
```

返回 `503` / `401` / `ModelNotOpen` 等均为验证失败，**不写配置，直接退出**。

### 执行切换（第二步）

验证通过后，脚本同时更新三处：

1. `model.default` / `provider` / `base_url` / `api_key`（主配置）
2. `custom_providers` 列表中的 provider 条目
3. `model_aliases` 中对应 alias 的 provider/base_url/model（避免路由断裂）

同时自动备份当前配置到 `~/.hermes/backups/`。

### 二次验证（第三步）

写入后重新读回 `config.yaml`，确认关键字段与预期一致。不一致时自动还原备份并报错。

## 切换命令

```bash
python3 ~/.hermes/bin/hermes_switch_model.py <标识>
```

| 标识 | 模型 | 实际 model 值 |
|------|------|---------------|
| `gpt` | GPT-5.4 | `gpt-5.4` |
| `glm` | GLM-5.1 | `GLM-5.1` |
| `minimax` | MiniMax-M2.7-highspeed | `MiniMax-M2.7-highspeed` |
| `ds` | DeepSeek-v4-flash | `deepseek-v4-flash` |

切换后**新会话生效**。

## 配置管理

### 添加新模型

用户提供 base_url、model_id、api_key，按规范生成命名并修改脚本。

**命名规范**：

| 信息 | 规则 | 示例 |
|------|------|------|
| provider name | `<平台>-<模型系列>` 全小写，中划线分隔 | `anthropic-claude` |
| env 变量 | `<平台>_<标识>_API_KEY` 全大写，下划线分隔 | `ANTHROPIC_API_KEY_CLAUDE` |
| alias | 简短英文小写 | `claude` |

**执行步骤**：

1. 生成变量名，写入 `~/.hermes/.env`
2. 在 `TARGETS` 字典添加条目（provider / base_url / verify_model / alias）
3. 在 `PROVIDER_DEFS` 列表添加 provider 定义
4. 在 `ALIAS_UPDATES` 列表添加别名同步条目
5. 本地提交

示例交互：

> 用户：「给我加一个 Claude 模型，baseurl 是 `https://api.anthropic.com/v1`，modelid 是 `claude-sonnet-4`，apikey 是 `sk-ant-xxx`」
>
> 我：「好，我来按规范添加。provider 命名为 `anthropic-claude`，变量名 `ANTHROPIC_API_KEY_CLAUDE`，alias `claude`。开始写入配置...」

### 删除模型

用户提供要删除的模型标识，从脚本三处移除对应条目：

1. `TARGETS` 字典
2. `PROVIDER_DEFS` 列表
3. `ALIAS_UPDATES` 列表

`.env` 中的 key 建议保留。

示例交互：

> 用户：「把 DeepSeek 从切换列表里删掉」
>
> 我：「好的，删除标识 `ds` 相关配置，`.env` 中的 key 保留。开始修改...」

### 修改模型配置

用户提供要改的模型和要改的内容，只修改对应字段。

**改 verify_model**：
只改 `TARGETS[<标识>]['verify_model']`，其他不动。

> 用户：「把 GLM 的验证模型改成 `glm-4-plus`」
>
> 我：「好，只改 verify_model 这一处，其他不动。开始修改...」

**改 API Key**：
修改 `~/.hermes/.env` 中对应变量的值。

> 用户：「换个 API Key，MiniMax 的 key 换成新值」
>
> 我：「好，修改 `.env` 中 `SVIPS_API_KEY_MINIMAX` 的值。开始写入...」

### 查看当前模型列表

读取 `~/.hermes/bin/hermes_switch_model.py`，提取 `TARGETS` 字典，输出格式化表格。

示例交互：

> 用户：「现在支持哪些模型？」
>
> 我：「当前支持4个模型：GPT-5.4 (gpt)、GLM-5.1 (glm)、MiniMax (minimax)、DeepSeek (ds)」

## 现有模型参考

| 标识 | provider | env 变量 |
|------|----------|----------|
| `gpt` | `custom:modelverse-gpt` | `MODELVERSE_API_KEY_GPT` |
| `glm` | `custom:svips-glm` | `SVIPS_API_KEY_GLM` |
| `minimax` | `custom:svips-minimax` | `SVIPS_API_KEY_MINIMAX` |
| `ds` | `custom:chudian-deepseek` | `CHUDIAN_API_KEY_DEEPSEEK` |

## 切换脚本结构

脚本中三处配置含义：

- **`TARGETS`**：切换目标配置（provider name、base_url、验证模型名、alias）
- **`PROVIDER_DEFS`**：custom_providers 列表中每个 provider 的完整定义（base_url、api_key、id）
- **`ALIAS_UPDATES`**：model_aliases 中每个 alias 需要同步更新的字段（provider、base_url、model）

切换时三处必须保持一致，删除时三处必须同时删除。

## 备份机制

每次切换前自动备份 `~/.hermes/config.yaml` 到 `~/.hermes/backups/hermes_config_YYYYMMDD_HHMMSS.yaml`。

切换后二次验证失败时自动还原备份，保证配置不会写坏。

## 故障排除

**切换后模型没变**：
- 确认是**新会话**（新开对话窗口），当前会话读取的是启动时的快照
- 检查 `config.yaml` 中 `model.default` 是否已更新

**验证通过但切换失败**：
- 查看 `~/.hermes/backups/` 是否有备份文件
- 检查 `config.yaml` 语法是否正确（`yaml.parse` 会报错）

**curl 预验证失败**：
- 检查 API Key 是否正确（参考 `tools/model-diagnosis.py`）
- 检查 base_url 是否正确
- 检查网络是否可达
