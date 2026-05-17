# Changelog

All notable changes to this project will be documented in this file.

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
