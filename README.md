# hermes-model-switch

Hermes Agent 模型切换工具集，支持多模型的一键切换、自动路由、增删改查管理。

## 组件概览

本仓库包含一组配套使用的技能：

| 技能 | 用途 | 触发词 |
|------|------|--------|
| `hermes-model-switch` | 手动切换模型 | 切换到 GPT / GLM / MiniMax / DeepSeek |
| `hermes-model-manage` | 模型的增删改查 | 加模型 / 删模型 / 改模型 / 查模型列表 |
| `env-param` | 修改 API Key 等参数 | 修改 env / 更新 API Key |

```
用户说"切换到GLM"  → hermes-model-switch
用户说"加一个新模型" → hermes-model-manage
用户说"换个API Key" → env-param
```

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

用户提供 base_url、model_id、api_key，我按规范生成变量名并修改脚本，步骤如下：

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

用户提供要删除的模型标识，我从 `TARGETS`、`PROVIDER_DEFS`、`ALIAS_UPDATES` 三处删除对应条目。

示例交互：

> 用户：「把 DeepSeek 从切换列表里删掉」
>
> 我：「好的，删除标识 `ds` 相关配置，同时保留 `.env` 中的 key 以备不时之需。开始修改...」

### 修改模型配置

用户提供要改的模型和要改的内容，我只修改对应的字段值。

示例交互：

> 用户：「把 GLM 的验证模型改成 `glm-4-plus`」
>
> 我：「好，只改 `TARGETS['glm']['verify_model']` 这一处，其他不动。开始修改...」

### 查看当前模型列表

直接读取脚本，提取 `TARGETS` 字典，输出格式化表格。

示例交互：

> 用户：「现在支持哪些模型？」
>
> 我：「当前支持4个模型：GPT-5.4 (gpt)、GLM-5.1 (glm)、MiniMax (minimax)、DeepSeek (ds)」

### 查看当前模型列表

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
│   └── hermes_switch_model.py   # 模型切换脚本
├── skill/
│   ├── hermes-model-switch/     # 切换技能文档
│   ├── hermes-model-manage/     # 增删改查技能文档
│   └── env-param/              # 环境变量修改文档
└── tools/
    └── model-diagnosis.py       # API Key 诊断工具
```

## 工作流程

```
用户消息
  │
  ├── "切换到GPT"       → hermes-model-switch  → 预验证 → 写配置
  ├── "加一个新模型"    → hermes-model-manage → 增删改
  └── "换个API Key"     → env-param           → 改 .env
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
