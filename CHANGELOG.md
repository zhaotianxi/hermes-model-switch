# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-05-17

### Added
- 重构为 Python package：`src/hermes_model_switch/`
- 新增结构化 CLI：`list` / `current` / `verify` / `switch` / `backup list` / `rollback`
- 新增 `--dry-run`
- 新增切换时文件锁，避免并发写配置
- 新增目录式备份与 `meta.json`
- 新增 example 配置文件
- 新增 pytest 测试
- 新增 GitHub Actions CI
- 新增 `pyproject.toml` 打包配置

### Changed
- 统一版本叙事为 semver
- 将三份模型配置合并为单一事实源 `MODEL_SPECS`
- 旧脚本 `scripts/hermes_switch_model.py` 改为兼容入口
- README / SKILL / references 全面同步到当前实现

### Fixed
- 修复 quickstart 过时描述
- 修复 SKILL 中错误的备份路径
- 清理旧版 provider / backup / CLI 表述漂移

## [1.0.0] - 2025-05-17

### Added
- 初始版本发布
- 支持 GPT-5.4 / GLM-5.1 / MiniMax-M2.7-highspeed / DeepSeek-v4-flash 四模型切换
- 预验证机制：切换前先验证模型可用性
- 自动回退：验证失败自动还原上一个可用版本
- model_aliases 同步更新
- 配置二次验证
- 自动备份机制

### Bug Fixes (历史积累)
- v6: model_aliases 未同步（导致别名路由断裂）
- v6: custom_providers 中 api_key 错误（GLM 请求用了 MiniMax 的 key）
- v6: yaml.safe_dump 丢失注释和格式
- v6: 回退逻辑用 mtime 排序改为文件名时间戳排序
- v7: find_prev_backup 内容自检（避免备份内容与文件名不匹配导致回退到错误模型）
- v7: 备份文件名改用源模型而非目标模型（避免备份文件名与内容永久错位）
