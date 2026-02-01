# Continuous Learning Skill

为 Cursor 提供持续学习能力，从用户与 AI 的交互中自动提取可复用的知识，生成新的技能文件供未来会话使用。

## 安装说明

### 安装步骤

安装此 Skill 需要完成以下两步：

#### 1. 安装脚本文件

将 `scripts/` 目录复制到 Cursor skills 目录：

```bash
# 全局安装（推荐，所有项目共享）
cp -r scripts/ ~/.cursor/skills/continuous-learning/scripts/

# 或项目级安装（仅当前项目使用）
cp -r scripts/ .cursor/skills/continuous-learning/scripts/
```

#### 2. 复制配置文件

```bash
cp default_config.json ~/.cursor/skills/continuous-learning/
```

### 验证安装

```bash
# 验证脚本安装
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --init
```

---

## 安装后提示

> **重要**：安装完成后，请将以下内容展示给用户。

---

✅ **Continuous Learning Skill 安装成功！**

### 下一步：启用规则

说 **"启用持续学习规则"** 开始使用。

或者手动执行：
```bash
python3 ~/.cursor/skills/continuous-learning/scripts/setup_rule.py '{"action": "enable"}'
```

### 快速开始

| 命令 | 说明 |
|------|------|
| `启用持续学习规则` | 开启自动学习功能（推荐） |
| `查看学习到的知识` | 查看本能和技能 |
| `演化本能` | 将本能聚合为技能 |

### 工作原理

1. **观察**：记录你与 AI 的交互过程
2. **检测**：识别可学习的模式（用户纠正、错误解决等）
3. **学习**：生成本能（原子化知识）
4. **演化**：将相关本能聚合为技能

### 首次使用提示

- 🆕 首次安装时没有历史数据，需要使用一段时间积累
- 💡 系统会自动学习你的工作习惯和偏好
- 🔒 所有数据存储在本地，不会上传到任何服务器

---

## 功能概述

### 核心能力

| 能力 | 说明 |
|------|------|
| **观察记录** | 记录会话中的关键动作和用户反馈 |
| **模式检测** | 识别用户纠正、错误解决、工具偏好等模式 |
| **本能生成** | 将检测到的模式转换为原子化的本能 |
| **技能演化** | 将相关本能聚合为完整的技能文档 |

### 学习的模式类型

| 模式类型 | 描述 | 示例 |
|---------|------|------|
| **用户纠正** | 用户纠正 AI 的行为 | "不要用 class，用函数" |
| **错误解决** | 特定错误的解决方案 | CORS 错误 → 配置 proxy |
| **工具偏好** | 用户偏好的工具/方法 | 偏好 pytest 而非 unittest |
| **项目规范** | 项目特定的约定 | API 路径使用 /api/v2 前缀 |

## 使用方式

### 自动模式（推荐）

启用规则后，系统会自动：
- 会话开始时加载学习历史
- 会话过程中记录关键动作
- 会话结束时保存并分析模式

### 手动命令

| 命令 | 描述 |
|------|------|
| `启用持续学习规则` | 创建自动学习规则 |
| `禁用持续学习规则` | 移除自动学习规则 |
| `更新持续学习规则` | 更新规则到最新版本 |
| `检查持续学习规则状态` | 检查规则是否已启用 |
| `查看学习到的知识` | 显示所有本能和技能 |
| `查看本能状态` | 显示本能的置信度和证据 |
| `演化本能` | 将相关本能聚合为技能 |
| `删除本能: xxx` | 删除特定本能 |
| `删除技能: xxx` | 删除演化生成的技能 |

## 脚本说明

### observe.py

观察脚本，管理会话生命周期。

```bash
# 会话开始时
python3 <skill_dir>/scripts/observe.py --init

# 记录观察
python3 <skill_dir>/scripts/observe.py --record '{
  "event": "tool_call",
  "tool": "Write",
  "input": {"file": "src/api.py"}
}'

# 会话结束时
python3 <skill_dir>/scripts/observe.py --finalize '{
  "topic": "会话主题",
  "summary": "会话摘要"
}'
```

### analyze.py

分析脚本，从观察记录中提取模式。

```bash
# 分析最近 7 天的会话
python3 <skill_dir>/scripts/analyze.py --recent 7

# 分析指定会话文件
python3 <skill_dir>/scripts/analyze.py --session <path>
```

### instinct.py

本能管理脚本。

```bash
# 查看所有本能
python3 <skill_dir>/scripts/instinct.py status

# 创建本能
python3 <skill_dir>/scripts/instinct.py create '{"id": "prefer-functional", "trigger": "编写新函数时", "domain": "code-style"}'

# 演化本能为技能
python3 <skill_dir>/scripts/instinct.py evolve

# 检查技能类型
python3 <skill_dir>/scripts/instinct.py --check-skill <name>

# 删除演化技能
python3 <skill_dir>/scripts/instinct.py --delete-skill <name>
```

### setup_rule.py

规则安装脚本。

```bash
# 启用规则
python3 <skill_dir>/scripts/setup_rule.py '{"action": "enable"}'

# 禁用规则
python3 <skill_dir>/scripts/setup_rule.py '{"action": "disable"}'

# 检查状态
python3 <skill_dir>/scripts/setup_rule.py '{"action": "check"}'

# 更新规则
python3 <skill_dir>/scripts/setup_rule.py '{"action": "update"}'
```

## 数据存储

```
continuous-learning-data/
├── observations/              # 观察记录
│   └── 2026-02/
│       └── obs_20260201_xxx.jsonl
├── instincts/                 # 本能文件
│   └── prefer-functional.yaml
├── evolved/                   # 演化生成的技能
│   ├── skills/
│   │   └── testing-workflow/
│   │       └── SKILL.md
│   ├── commands/
│   └── skills-index.json
├── profile/                   # 学习档案
│   └── learning_profile.json
└── config.json                # 用户配置
```

## 配置选项

配置文件位于数据目录的 `config.json`。

```json
{
  "version": "1.0",
  "enabled": true,
  "observation": {
    "enabled": true,
    "retention_days": 90
  },
  "detection": {
    "enabled": true,
    "min_evidence_count": 2
  },
  "instincts": {
    "min_confidence": 0.3,
    "auto_apply_threshold": 0.7,
    "max_instincts": 100
  },
  "evolution": {
    "enabled": true,
    "cluster_threshold": 3,
    "auto_evolve": false
  }
}
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enabled` | `true` | 总开关 |
| `observation.retention_days` | `90` | 观察记录保留天数 |
| `detection.min_evidence_count` | `2` | 最少证据数才创建本能 |
| `instincts.min_confidence` | `0.3` | 最低置信度 |
| `instincts.auto_apply_threshold` | `0.7` | 自动应用阈值 |
| `evolution.cluster_threshold` | `3` | 演化所需最少本能数 |

## 隐私说明

- 所有数据存储在本地
- 不上传任何信息到服务器
- 用户可以随时删除学习数据
- 本能文件不包含实际代码，只包含模式描述

## 与行为预测的区别

| 维度 | 持续学习 | 行为预测 |
|------|---------|---------|
| **核心问题** | AI 应该**怎么做**？ | 用户想**做什么**？ |
| **学习对象** | 解决问题的**方法和知识** | 用户的**工作流程和习惯** |
| **输出目标** | 生成**新的技能/知识** | 生成**预测和建议** |
| **应用方向** | 让 AI **更专业** | 让 AI **更贴心** |

两者是互补关系，可以同时使用。
