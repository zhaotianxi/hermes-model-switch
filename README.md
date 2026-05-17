# hermes-model-switch

Hermes Agent 模型切换工具，支持 GPT / GLM / MiniMax / DeepSeek 一键切换，带预验证 + 自动回退。

## 功能特性

- **预验证切换**：切换前先 curl 验证目标模型是否可达，不可达不写配置
- **自动回退**：验证失败自动回退到上一个可用版本
- **model_aliases 同步**：切换时同步更新别名路由，避免请求走错 provider
- **配置二次验证**：写入后重新读回确认关键字段正确
- **备份机制**：每次切换自动备份，保留历史版本

## 支持的模型

| 模型 | 标识 | 供应商 |
|------|------|--------|
| GPT-5.4 | `gpt` | modelverse.cn |
| GLM-5.1 | `glm` | svips.org |
| MiniMax | `minimax` | svips.org |
| DeepSeek | `ds` | chudian.site |

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

## 使用方法

```bash
python3 ~/.hermes/bin/hermes_switch_model.py gpt      # 切换到 GPT-5.4
python3 ~/.hermes/bin/hermes_switch_model.py glm      # 切换到 GLM-5.1
python3 ~/.hermes/bin/hermes_switch_model.py minimax  # 切换到 MiniMax
python3 ~/.hermes/bin/hermes_switch_model.py ds       # 切换到 DeepSeek
```

切换后**新会话生效**，当前会话不保证热切换。

## 配置要求

- API Key 配置在 `~/.hermes/.env` 中，脚本自动从 `.env` 读取
- `~/.hermes/config.yaml` 为目标配置文件
- `~/.hermes/backups/` 为自动备份目录

## API Key 环境变量名

| 模型 | 环境变量 |
|------|----------|
| GPT-5.4 | `MODELVERSE_API_KEY_GPT` |
| GLM-5.1 | `SVIPS_API_KEY_GLM` |
| MiniMax | `SVIPS_API_KEY_MINIMAX` |
| DeepSeek | `CHUDIAN_API_KEY_DEEPSEEK` |

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
# 1. 更新 CHANGELOG.md，标注版本号和变更内容
# 2. 打 tag
git tag -a v1.0.0 -m "v1.0.0: 初始发布"
# 3. 推送 tag
git push origin v1.0.0
```

## License

MIT
