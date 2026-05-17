# Hermes Model Switch Improvement Plan

> For Hermes: implement directly in this session with verification after each major milestone.

**Goal:** 完成 hermes-model-switch 仓库 11 项核心优化，包括文档一致性、单一配置源、CLI 增强、dry-run、锁、示例、测试、打包与 CI。

**Architecture:** 保留仓库现有用途，但把核心逻辑从单文件脚本整理成可测试的 Python package。继续提供兼容入口脚本，同时新增结构化 CLI 与自动化测试/CI。文档统一以当前实现为准，消除 README / SKILL / references 漂移。

**Tech Stack:** Python 3.9+, argparse, pathlib, tempfile/pytest, GitHub Actions, ruamel.yaml / PyYAML

---

## Task 1: 盘点现状并确定改造边界
**Objective:** 锁定要改的文件和保留的兼容面。

**Files:**
- Read: `README.md`
- Read: `CHANGELOG.md`
- Read: `scripts/hermes_switch_model.py`
- Read: `skill/hermes-model-switch/SKILL.md`
- Read: `skill/hermes-model-switch/references/*.md`

**Steps:**
1. 记录文档漂移项
2. 记录 CLI / 逻辑缺失项
3. 明确兼容入口：保留 `scripts/hermes_switch_model.py`

## Task 2: 设计单一事实源模型配置
**Objective:** 用一个 central spec 代替 TARGETS/PROVIDER_DEFS/ALIAS_UPDATES 三份重复配置。

**Files:**
- Create: `src/hermes_model_switch/model_specs.py`

**Steps:**
1. 定义 `MODEL_SPECS`
2. 提供派生函数：main model config / provider def / alias update
3. 提供 mode <-> default 互转工具

## Task 3: 拆分核心逻辑模块
**Objective:** 把 YAML、验证、备份、锁、CLI 逻辑拆分为独立模块。

**Files:**
- Create: `src/hermes_model_switch/config_io.py`
- Create: `src/hermes_model_switch/backup.py`
- Create: `src/hermes_model_switch/verify.py`
- Create: `src/hermes_model_switch/locking.py`
- Create: `src/hermes_model_switch/cli.py`
- Create: `src/hermes_model_switch/__init__.py`

**Steps:**
1. 抽出 env/config 读写
2. 抽出 backup metadata 与 rollback
3. 抽出 model verify
4. 抽出 file lock
5. 组装 argparse CLI

## Task 4: 保留兼容脚本入口
**Objective:** 旧命令仍可用，同时内部走新 package。

**Files:**
- Modify: `scripts/hermes_switch_model.py`

**Steps:**
1. 变成薄包装器
2. 兼容 `python3 ~/.hermes/bin/hermes_switch_model.py gpt`
3. 支持新子命令透传

## Task 5: 增加 CLI 功能
**Objective:** 实现 current/list/verify/switch/backup list/rollback/dry-run。

**Files:**
- Modify: `src/hermes_model_switch/cli.py`

**Steps:**
1. `list`
2. `current`
3. `verify <mode>`
4. `switch <mode> [--dry-run]`
5. `backup list`
6. `rollback <backup_id>`

## Task 6: 修正文档漂移
**Objective:** README / SKILL / references / CHANGELOG 统一。

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `skill/hermes-model-switch/SKILL.md`
- Modify: `skill/hermes-model-switch/references/quickstart.md`
- Modify: `skill/hermes-model-switch/references/bug5-backup-content-mismatch.md`

**Steps:**
1. 统一版本叙事为 semver
2. 统一备份格式说明
3. 删除过时 provider / custom 描述
4. 新增项目边界、安装、示例、CLI 说明

## Task 7: 增加示例与打包
**Objective:** 让仓库开箱更完整。

**Files:**
- Create: `examples/config.yaml.example`
- Create: `examples/.env.example`
- Create: `pyproject.toml`

**Steps:**
1. 提供最小配置示例
2. 配置 console script
3. 声明依赖和 pytest extra

## Task 8: 增加自动化测试
**Objective:** 覆盖关键逻辑与回归场景。

**Files:**
- Create: `tests/test_model_specs.py`
- Create: `tests/test_backup.py`
- Create: `tests/test_switch_flow.py`
- Create: `tests/conftest.py`

**Steps:**
1. 测试 mode/default 映射
2. 测试 backup metadata 与回退查找
3. 测试 dry-run 不落盘
4. 测试 switch 写入 alias/provider/main config
5. 测试验证失败回退

## Task 9: 增加 GitHub Actions
**Objective:** 自动跑编译、测试。

**Files:**
- Create: `.github/workflows/ci.yml`

**Steps:**
1. 安装依赖
2. 运行 py_compile
3. 运行 pytest

## Task 10: 运行验证
**Objective:** 用真实命令验证改造结果。

**Files:**
- Validate repo

**Steps:**
1. `python3 -m py_compile ...`
2. `pytest`
3. CLI smoke tests
4. 文档交叉检查

## Task 11: 输出最终变更说明
**Objective:** 总结已完成的 11 项优化与后续可选项。

**Files:**
- Report in final response
