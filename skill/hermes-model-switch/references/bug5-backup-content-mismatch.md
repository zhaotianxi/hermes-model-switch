# Bug 5 Fix: find_prev_backup 历史问题说明

**说明**：这份文档保留历史背景，帮助理解为什么项目后来引入了更稳妥的目录式备份与 metadata。

## 历史问题

旧实现曾使用：

```text
~/.hermes/backups/config.yaml.<mode>.bak-<timestamp>
```

并依赖：
- 文件名中的 mode
- 备份内容中的 `model.default`
- 时间戳排序

在手工覆盖、并发写、或错误命名场景下，可能出现：
- 文件名声明的模型与内容不一致
- 回退命中了错误备份

## 历史修复

v7 曾通过“读取备份内容后自检 `model.default`”缓解该问题。

## 现状（1.1.0 起）

当前项目已经进一步升级为目录式备份：

```text
~/.hermes/backups/<backup_id>/
  config.yaml
  meta.json
```

`meta.json` 中保存：
- `backup_id`
- `created_at`
- `source_default`
- `source_mode`
- `target_mode`

这样做的好处：
- 不再强依赖文件名约定
- 便于审计和回退
- 更容易扩展 smoke test / rollback 策略

## 结论

这份文档主要用于保留历史上下文。当前实现优先参考 README、SKILL.md 和 `src/hermes_model_switch/` 中的代码。
