---
name: skill-store
description: |
  发现、管理和分发 Cursor Skill 的包管理器。配置 Git 仓库源，自动同步索引，
  自然语言搜索推荐，支持项目级和全局安装与版本更新。当用户需要安装、更新、
  搜索 Skill，或配置 Skill 仓库源时使用。
---

# Skill Store

Cursor Skill 包管理器：从 Git 仓库发现、安装和更新 Skill。

## 安装 / 更新 / 卸载

```bash
python3 skills/skill-store/main.py install --target ~/.cursor/skills/skill-store
python3 skills/skill-store/main.py update --target ~/.cursor/skills/skill-store
python3 skills/skill-store/main.py uninstall --target ~/.cursor/skills/skill-store
```

## 核心流程

```
1. registry add  → 添加 Git 仓库源
2. sync all      → Clone/Pull 同步仓库
3. index rebuild → 构建本地 Skill 索引
4. index search  → 搜索可用 Skill
5. install       → 安装 Skill（含依赖解析）
6. hook          → 会话启动自动检查更新
```

## CLI 命令

所有命令在 `scripts/` 目录下，输出 JSON 格式。

### 仓库管理

```bash
# 添加仓库源
python3 scripts/registry.py add --url "https://github.com/user/repo" --alias "my-skills"

# 列出所有仓库源
python3 scripts/registry.py list

# 移除仓库源
python3 scripts/registry.py remove --alias "my-skills"
```

### 同步

```bash
# 同步所有仓库
python3 scripts/sync.py all

# 同步指定仓库
python3 scripts/sync.py one --alias "my-skills"
```

### 索引

```bash
# 重建索引
python3 scripts/index.py rebuild

# 搜索 Skill
python3 scripts/index.py search --query "pdf processing"

# 列出所有可用 Skill
python3 scripts/index.py list
```

### 安装管理

```bash
# 安装 Skill（全局）
python3 scripts/install.py install --name "pdf-processor" --scope global

# 安装 Skill（项目级）
python3 scripts/install.py install --name "pdf-processor" --scope project

# 更新 Skill
python3 scripts/install.py update --name "pdf-processor"

# 更新所有
python3 scripts/install.py update-all

# 卸载 Skill
python3 scripts/install.py uninstall --name "pdf-processor"

# 查看已安装
python3 scripts/install.py list
```

### 状态查询

```bash
python3 scripts/status.py
python3 scripts/status.py updates
```

## 自主决策指南

| 用户说 | 执行 |
|--------|------|
| "添加仓库 URL" | `registry.py add` → `sync.py all` → `index.py rebuild` |
| "同步仓库" / "检查更新" | `sync.py all` → `index.py rebuild` → `status.py updates` |
| "我需要一个处理 PDF 的 Skill" | `index.py search --query "pdf"` → 展示结果推荐 |
| "安装 xxx" | `install.py install --name xxx` |
| "更新 xxx" / "更新所有" | `install.py update --name xxx` 或 `install.py update-all` |
| "卸载 xxx" | `install.py uninstall --name xxx` |
| "查看已安装的 Skill" | `install.py list` |
| "查看状态" | `status.py` |

## 会话 Hook

安装后自动注册 `skill-store-hook.mdc`（alwaysApply），每次会话启动时：
1. 读取上次同步结果，展示更新提示
2. 如果今天未同步，异步启动后台同步

## 依赖解析

Skill 在 SKILL.md frontmatter 中声明依赖：

```yaml
---
name: web-automation-builder
dependencies:
  - playwright
  - agent-interact
---
```

安装时自动解析并递归安装依赖，支持循环依赖检测。

## 触发词

- 安装 skill、添加 skill、搜索 skill
- 更新 skill、卸载 skill
- 添加仓库、配置仓库源
- 同步仓库、检查更新
- 查看已安装、skill 状态
