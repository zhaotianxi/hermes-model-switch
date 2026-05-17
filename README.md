# hermes-model-switch

Hermes Agent 大模型配置管理工具，支持模型切换和增删改查。

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

# 安装切换脚本
mkdir -p ~/.hermes/bin
cp scripts/hermes_switch_model.py ~/.hermes/bin/
chmod +x ~/.hermes/bin/hermes_switch_model.py
```

## 配置架构

**`.env`**：存放 API Key 等敏感信息，**不提交到仓库**

**`~/.hermes/config.yaml`**：引用 `.env` 中的变量（`${VAR_NAME}`），安全可分享

```
~/.hermes/
├── .env          # API Key 等敏感配置
└── config.yaml   # 主配置，引用 .env 中的变量
```

## 切换流程（详细说明）

切换操作分三步执行，**验证失败不写配置，保持现状**：

### 第一步：预验证

用 curl 测试目标模型是否可达，返回含 `"choices"` 即为通过。

```bash
# 示例：验证 MiniMax
curl -s https://api.svips.org/v1/chat/completions \
  -H "Authorization: Bearer $SVIPS_API_KEY_MINIMAX" \
  -H "Content-Type: application/json" \
  -d '{"model":"MiniMax-M2.7-highspeed","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
```

返回 `503` / `401` / `ModelNotOpen` 等均为验证失败，**不写配置，直接退出**。

### 第二步：写入配置 + 同步 model_aliases

验证通过后，脚本同时更新三处：
1. `model.default` / `provider` / `base_url` / `api_key`（主配置）
2. `custom_providers` 列表中的 provider 条目
3. `model_aliases` 中对应 alias 的 provider/base_url/model（避免路由断裂）

同时自动备份当前配置到 `~/.hermes/backups/`。

### 第三步：二次验证

写入后重新读回 `config.yaml`，确认关键字段（default / provider / api_key）与预期一致。不一致时自动还原备份并报错，**保证配置不会写坏**。

### 完整流程图

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

## 快速使用

### 切换模型

```bash
python3 ~/.hermes/bin/hermes_switch_model.py <标识>
```

| 标识 | 模型 |
|------|------|
| `gpt` | GPT-5.4 |
| `glm` | GLM-5.1 |
| `minimax` | MiniMax-M2.7-highspeed |
| `ds` | DeepSeek-v4-flash |

切换后**新会话生效**。

### 添加新模型

用户提供 base_url、model_id、api_key，我按规范生成变量名并修改脚本：

**1. 生成命名**（遵循现有规范）：

| 信息 | 规则 | 示例 |
|------|------|------|
| provider name | `<平台>-<模型系列>` 全小写 | `anthropic-claude` |
| env 变量 | `<平台>_<标识>_API_KEY` 全大写 | `ANTHROPIC_API_KEY_CLAUDE` |
| alias | 简短英文小写 | `claude` |

**2. 写入 `.env`** → **3. 修改脚本三处配置** → **4. 验证** → **5. 本地提交**

示例交互：

> 用户：「给我加一个 Claude 模型，baseurl 是 `https://api.anthropic.com/v1`，modelid 是 `claude-sonnet-4`，apikey 是 `sk-ant-xxx`」
>
> 我：「好，我来按规范添加。provider 命名为 `anthropic-claude`，变量名 `ANTHROPIC_API_KEY_CLAUDE`，alias `claude`。开始写入配置...」

### 删除模型

用户提供要删除的模型标识，从 `TARGETS`、`PROVIDER_DEFS`、`ALIAS_UPDATES` 三处删除对应条目，`.env` 中的 key 建议保留。

示例交互：

> 用户：「把 DeepSeek 从切换列表里删掉」
>
> 我：「好的，删除标识 `ds` 相关配置，`.env` 中的 key 保留。开始修改...」

### 修改模型配置

用户提供要改的模型和要改的内容，只修改对应的字段值。

示例交互：

> 用户：「把 GLM 的验证模型改成 `glm-4-plus`」
>
> 我：「好，只改 `TARGETS['glm']['verify_model']` 这一处，其他不动。开始修改...」

> 用户：「换个 API Key，MiniMax 的 key 换成 `sk-new-key-xxx`」
>
> 我：「好，修改 `.env` 中 `SVIPS_API_KEY_MINIMAX` 的值。开始写入...」

### 查看当前模型列表

直接读取脚本，提取 `TARGETS` 字典，输出格式化表格。

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

**命名规范（新增模型时遵循）**：

- **provider name**：`平台-模型系列`，全小写，中划线
- **env 变量**：`平台_标识_API_KEY`，全大写，下划线
- **alias**：简短英文小写

## 目录结构

```
hermes-model-switch/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── scripts/
│   └── hermes_switch_model.py   # 模型切换脚本（含增删改查逻辑）
├── skill/
│   └── hermes-model-switch/    # 完整技能文档（切换 + 增删改查）
│       └── SKILL.md
└── tools/
    └── model-diagnosis.py       # API Key 诊断工具
```

## 开发约定

- 所有变更**本地提交**后再按需 push
- push 前验证切换脚本可正常执行
- 配置文件用 `${VAR_NAME}` 引用，不直接写 key

```bash
# 本地提交
git add . && git commit -m "描述"

# 发布新版本
git tag -a v1.1.0 -m "v1.1.0: ..."
git push && git push --tags
```

## License

MIT
