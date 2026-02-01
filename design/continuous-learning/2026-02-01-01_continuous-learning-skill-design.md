# Continuous Learning Skill 设计文档

## 1. 概述

**Skill 名称**: continuous-learning  
**描述**: 为 Cursor 提供持续学习能力，从用户与 AI 的交互中自动提取可复用的知识，生成新的技能文件供未来会话使用。

### 1.1 问题背景

Cursor 目前存在以下限制：
- AI 无法从用户纠正中学习改进
- 每次遇到相同问题都需要重新解决
- 无法积累项目特定的解决方案
- 用户的偏好和习惯无法被持久化学习

### 1.2 解决方案

创建一个 Continuous Learning Skill，实现：
- 观察用户与 AI 的交互过程
- 检测可学习的模式（用户纠正、错误解决、工作流程等）
- 生成可复用的技能文件
- 在未来会话中自动应用学习到的知识

### 1.3 核心原则

- **零外部依赖**：只使用 Python 标准库
- **规则驱动**：通过 Cursor Rules 指导 AI 主动调用脚本
- **代码数据分离**：Skill 代码可更新，学习数据永不覆盖
- **本地存储**：所有数据存储在本地，不上传到任何服务器
- **渐进学习**：从简单的模式开始，逐步积累知识

### 1.4 与行为预测的区别

| 维度 | 持续学习 | 行为预测 |
|------|---------|---------|
| **核心问题** | AI 应该**怎么做**？ | 用户想**做什么**？ |
| **学习对象** | 解决问题的**方法和知识** | 用户的**工作流程和习惯** |
| **输出目标** | 生成**新的技能/知识** | 生成**预测和建议** |
| **应用方向** | 让 AI **更专业** | 让 AI **更贴心** |

---

## 2. 核心功能

### 2.1 观察记录（Observation Recording）

- **会话开始时**：初始化观察会话，加载已学习的知识
- **会话过程中**：记录关键动作（工具调用、用户反馈等）
- **会话结束时**：保存观察记录，触发模式分析

### 2.2 模式检测（Pattern Detection）

检测以下类型的可学习模式：

| 模式类型 | 描述 | 示例 |
|---------|------|------|
| **用户纠正** | 用户纠正 AI 的行为 | "不要用 class，用函数" |
| **错误解决** | 特定错误的解决方案 | CORS 错误 → 配置 proxy |
| **工具偏好** | 用户偏好的工具/方法 | 偏好 pytest 而非 unittest |
| **项目规范** | 项目特定的约定 | API 路径使用 /api/v2 前缀 |
| **调试技巧** | 有效的调试方法 | 使用 console.table 调试数组 |

### 2.3 知识生成（Knowledge Generation）

将检测到的模式转换为可复用的知识文件：

- **本能（Instinct）**：原子化的学习行为，带置信度评分
- **技能（Skill）**：综合多个本能的完整技能文档

### 2.4 知识应用（Knowledge Application）

- **自动加载**：会话开始时加载相关知识
- **上下文注入**：将知识作为上下文提供给 AI
- **行为调整**：AI 根据学习到的知识调整行为

---

## 3. 存储架构

### 3.1 目录结构

```
~/.cursor/skills/
├── continuous-learning/           # Skill 代码（可安全更新）
│   ├── SKILL.md                   # Skill 入口文件
│   ├── rules/
│   │   └── continuous-learning.mdc  # 规则文件
│   ├── scripts/
│   │   ├── observe.py             # 观察脚本（init/record/finalize）
│   │   ├── analyze.py             # 模式分析脚本
│   │   ├── instinct.py            # 本能管理脚本
│   │   └── utils.py               # 工具函数
│   ├── default_config.json        # 默认配置模板
│   └── tests/                     # 测试文件
│
└── continuous-learning-data/      # 用户数据（永不覆盖）
    ├── observations/              # 观察记录
    │   └── 2026-02/
    │       └── obs_20260201_001.jsonl
    ├── instincts/                 # 本能文件
    │   └── prefer-functional.yaml
    ├── evolved/                   # 演化生成的技能
    │   ├── skills/
    │   │   └── testing-workflow/
    │   │       └── SKILL.md
    │   └── commands/
    ├── profile/                   # 学习档案
    │   └── learning_profile.json
    └── config.json                # 用户自定义配置
```

### 3.2 数据文件格式

#### 观察记录 (observations/*.jsonl)

```jsonl
{"timestamp":"2026-02-01T10:30:00Z","event":"tool_call","tool":"Write","input":{"file":"src/api.py"},"stage":"implement"}
{"timestamp":"2026-02-01T10:30:05Z","event":"user_feedback","type":"correction","content":"不要用 class，用函数"}
{"timestamp":"2026-02-01T10:31:00Z","event":"tool_call","tool":"StrReplace","input":{"file":"src/api.py"},"stage":"implement"}
```

#### 本能文件 (instincts/*.yaml)

```yaml
---
id: prefer-functional-style
trigger: "编写新函数时"
confidence: 0.7
domain: "代码风格"
source: "会话观察"
created_at: "2026-02-01T10:35:00Z"
updated_at: "2026-02-01T10:35:00Z"
evidence_count: 3
---

# 偏好函数式风格

## 行为
在适当的情况下使用函数式模式而非类。

## 证据
- 用户在 2026-02-01 纠正了基于类的方法，改为函数式
- 观察到 3 次函数式模式偏好
```

#### 演化技能 (evolved/skills/*/SKILL.md)

```markdown
---
name: testing-workflow
description: 综合测试工作流技能
evolved_from:
  - always-test-first (置信度: 0.9)
  - prefer-pytest (置信度: 0.85)
evolved_at: "2026-02-01T12:00:00Z"
---

# 测试工作流技能

## 触发条件
当用户进行测试相关任务时触发。

## 工作流程
1. 先写测试用例（TDD 方式）
2. 使用 pytest 作为测试框架
3. 每次代码修改后运行测试

## 最佳实践
- 测试覆盖率应 > 80%
- 使用 fixtures 进行通用设置
- 参数化相似的测试用例
```

### 3.3 演化技能的识别机制

#### 问题背景

Cursor 不会自动扫描 `continuous-learning-data/evolved/skills/` 目录中的技能文件。需要设计一套机制让 Cursor 能够识别和使用这些演化生成的技能。

#### 识别流程

```
┌─────────────────────────────────────────────────────────┐
│                    演化技能生成                          │
│                                                         │
│   instinct.py --evolve                                  │
│   ↓                                                     │
│   检测可聚合的本能                                       │
│   ↓                                                     │
│   生成技能文件到 evolved/skills/                         │
│                                                         │
└────────────────────────────┬────────────────────────────┘
                             │
                             │ 同步到 Cursor skills 目录
                             ▼
┌─────────────────────────────────────────────────────────┐
│                    技能同步机制                          │
│                                                         │
│   方式 1：符号链接（推荐）                               │
│   ln -s ~/.cursor/skills/continuous-learning-data/      │
│          evolved/skills/testing-workflow                │
│          ~/.cursor/skills/evolved-testing-workflow      │
│                                                         │
│   方式 2：复制到 skills 目录                             │
│   cp -r evolved/skills/testing-workflow                 │
│          ~/.cursor/skills/evolved-testing-workflow      │
│                                                         │
└────────────────────────────┬────────────────────────────┘
                             │
                             │ Cursor 识别
                             ▼
┌─────────────────────────────────────────────────────────┐
│                    Cursor 加载技能                       │
│                                                         │
│   ~/.cursor/skills/                                     │
│   ├── continuous-learning/        # 持续学习 skill      │
│   ├── behavior-prediction/        # 行为预测 skill      │
│   └── evolved-testing-workflow/   # 演化生成的技能      │
│       └── SKILL.md                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 自动同步实现

在 `instinct.py --evolve` 命令中，自动将生成的技能同步到 Cursor skills 目录：

```python
def sync_evolved_skill_to_cursor(skill_name: str, skill_path: Path):
    """
    将演化生成的技能同步到 Cursor skills 目录
    
    Args:
        skill_name: 技能名称
        skill_path: 技能文件路径
    """
    cursor_skills_dir = Path.home() / ".cursor" / "skills"
    target_dir = cursor_skills_dir / f"evolved-{skill_name}"
    
    # 如果目标已存在，先删除
    if target_dir.exists():
        shutil.rmtree(target_dir)
    
    # 复制技能目录
    shutil.copytree(skill_path, target_dir)
    
    print(f"✅ 技能已同步到: {target_dir}")
```

#### 技能文件格式要求

为了让 Cursor 正确识别演化技能，技能文件必须遵循以下格式：

```
evolved/skills/<skill-name>/
└── SKILL.md                    # 必须有 SKILL.md 文件
```

SKILL.md 文件格式：

```markdown
---
name: <skill-name>
description: <技能描述>
---

# <技能标题>

## 触发条件
<何时触发此技能>

## 使用方式
<如何使用此技能>

## 相关命令
<可选：相关的命令>
```

#### 技能加载时机

| 时机 | 加载方式 | 说明 |
|------|---------|------|
| **会话开始** | 自动加载 | `--init` 时检查并加载相关技能 |
| **用户提及** | 按需加载 | 用户提到 @skill-name 时加载 |
| **任务匹配** | 智能加载 | AI 检测到相关任务时加载 |

#### 技能索引机制

为了快速查找相关技能，维护一个技能索引文件：

```json
// continuous-learning-data/evolved/skills-index.json
{
  "skills": [
    {
      "name": "testing-workflow",
      "path": "evolved/skills/testing-workflow",
      "cursor_path": "~/.cursor/skills/evolved-testing-workflow",
      "triggers": ["测试", "test", "pytest", "unittest"],
      "domains": ["testing", "workflow"],
      "evolved_at": "2026-02-01T12:00:00Z",
      "synced": true
    }
  ],
  "last_updated": "2026-02-01T12:00:00Z"
}
```

#### 会话开始时的技能加载流程

```python
def load_relevant_skills(user_message: str) -> list:
    """
    根据用户消息加载相关的演化技能
    
    流程：
    1. 读取技能索引
    2. 匹配用户消息中的关键词
    3. 加载匹配的技能内容
    4. 返回技能摘要供 AI 使用
    """
    # 1. 读取技能索引
    index = load_skills_index()
    
    # 2. 匹配关键词
    matched_skills = []
    for skill in index["skills"]:
        for trigger in skill["triggers"]:
            if trigger.lower() in user_message.lower():
                matched_skills.append(skill)
                break
    
    # 3. 加载技能内容
    skills_content = []
    for skill in matched_skills:
        skill_path = Path(skill["cursor_path"]).expanduser() / "SKILL.md"
        if skill_path.exists():
            content = skill_path.read_text()
            skills_content.append({
                "name": skill["name"],
                "content": content
            })
    
    return skills_content
```

#### 完整的演化和同步流程

```
1. 用户执行 "演化本能" 命令
   ↓
2. instinct.py --evolve 分析本能聚类
   ↓
3. 生成技能文件到 evolved/skills/<skill-name>/SKILL.md
   ↓
4. 自动同步到 ~/.cursor/skills/evolved-<skill-name>/
   ↓
5. 更新技能索引 evolved/skills-index.json
   ↓
6. 下次会话开始时，--init 加载技能索引
   ↓
7. 根据用户消息匹配相关技能
   ↓
8. 将技能内容作为上下文提供给 AI
```

### 3.4 技能删除机制

#### 删除场景

| 场景 | 触发方式 | 说明 |
|------|---------|------|
| **用户主动删除** | `删除技能: <skill-name>` | 用户认为技能不再有用 |
| **本能置信度过低** | 自动清理 | 支撑技能的本能置信度都低于阈值 |
| **技能过期** | 定期清理 | 长时间未被使用的技能 |

#### 删除流程

```
1. 用户执行 "删除技能: testing-workflow" 命令
   ↓
2. instinct.py --delete-skill testing-workflow
   ↓
3. 删除源文件: evolved/skills/testing-workflow/
   ↓
4. 删除 Cursor 中的同步文件/链接: ~/.cursor/skills/evolved-testing-workflow/
   ↓
5. 更新技能索引: 从 skills-index.json 中移除
   ↓
6. 可选：保留或删除相关本能
```

#### 删除实现

```python
def delete_evolved_skill(skill_name: str, delete_instincts: bool = False) -> dict:
    """
    删除演化生成的技能
    
    Args:
        skill_name: 技能名称
        delete_instincts: 是否同时删除相关本能
    
    Returns:
        删除结果
    """
    result = {
        "status": "success",
        "deleted": [],
        "errors": []
    }
    
    # 1. 删除源文件
    evolved_path = get_data_dir() / "evolved" / "skills" / skill_name
    if evolved_path.exists():
        shutil.rmtree(evolved_path)
        result["deleted"].append(f"源文件: {evolved_path}")
    
    # 2. 删除 Cursor 中的同步文件/链接
    cursor_path = Path.home() / ".cursor" / "skills" / f"evolved-{skill_name}"
    if cursor_path.exists():
        if cursor_path.is_symlink():
            cursor_path.unlink()  # 删除符号链接
            result["deleted"].append(f"符号链接: {cursor_path}")
        else:
            shutil.rmtree(cursor_path)  # 删除复制的目录
            result["deleted"].append(f"同步目录: {cursor_path}")
    
    # 3. 更新技能索引
    index_path = get_data_dir() / "evolved" / "skills-index.json"
    if index_path.exists():
        index = json.loads(index_path.read_text())
        index["skills"] = [s for s in index["skills"] if s["name"] != skill_name]
        index["last_updated"] = get_timestamp()
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2))
        result["deleted"].append("技能索引已更新")
    
    # 4. 可选：删除相关本能
    if delete_instincts:
        deleted_instincts = delete_related_instincts(skill_name)
        result["deleted"].extend(deleted_instincts)
    
    return result


def delete_related_instincts(skill_name: str) -> list:
    """
    删除与技能相关的本能
    
    通过读取技能的 evolved_from 字段，找到相关本能并删除
    """
    deleted = []
    
    # 读取技能的 evolved_from 信息
    skill_path = get_data_dir() / "evolved" / "skills" / skill_name / "SKILL.md"
    if not skill_path.exists():
        return deleted
    
    # 解析 frontmatter 获取 evolved_from
    content = skill_path.read_text()
    evolved_from = parse_evolved_from(content)
    
    # 删除相关本能
    for instinct_id in evolved_from:
        instinct_path = get_data_dir() / "instincts" / f"{instinct_id}.yaml"
        if instinct_path.exists():
            instinct_path.unlink()
            deleted.append(f"本能: {instinct_id}")
    
    return deleted
```

#### 自动清理机制

除了用户主动删除，系统还支持自动清理：

```python
def auto_cleanup_skills(config: dict) -> dict:
    """
    自动清理过期或无效的技能
    
    清理条件：
    1. 支撑本能的平均置信度 < min_confidence
    2. 技能超过 retention_days 未被使用
    """
    result = {"cleaned": [], "kept": []}
    
    index = load_skills_index()
    min_confidence = config.get("instincts", {}).get("min_confidence", 0.3)
    retention_days = config.get("evolution", {}).get("retention_days", 180)
    
    for skill in index["skills"]:
        # 检查本能置信度
        avg_confidence = calculate_skill_confidence(skill["name"])
        
        # 检查最后使用时间
        last_used = skill.get("last_used")
        days_since_used = calculate_days_since(last_used) if last_used else float('inf')
        
        # 判断是否需要清理
        should_clean = (
            avg_confidence < min_confidence or
            days_since_used > retention_days
        )
        
        if should_clean:
            delete_evolved_skill(skill["name"])
            result["cleaned"].append({
                "name": skill["name"],
                "reason": f"置信度={avg_confidence:.2f}, 未使用天数={days_since_used}"
            })
        else:
            result["kept"].append(skill["name"])
    
    return result
```

#### 删除确认机制

为了防止误删，删除操作需要用户确认：

```python
def handle_delete_skill(skill_name: str, confirm: bool = False) -> dict:
    """
    处理技能删除请求
    
    如果 confirm=False，返回待删除内容供用户确认
    如果 confirm=True，执行删除
    """
    if not confirm:
        # 返回待删除内容
        return {
            "status": "pending_confirmation",
            "skill_name": skill_name,
            "will_delete": [
                f"技能文件: evolved/skills/{skill_name}/",
                f"Cursor 同步: ~/.cursor/skills/evolved-{skill_name}/",
                "技能索引条目"
            ],
            "message": f"确认删除技能 '{skill_name}'？请说 '确认删除' 或 '取消'"
        }
    else:
        # 执行删除
        return delete_evolved_skill(skill_name)
```

#### 用户交互示例

```
用户: 删除技能: testing-workflow

AI: 即将删除技能 'testing-workflow'，将删除以下内容：
    - 技能文件: evolved/skills/testing-workflow/
    - Cursor 同步: ~/.cursor/skills/evolved-testing-workflow/
    - 技能索引条目
    
    是否同时删除相关本能？
    - always-test-first (置信度: 0.9)
    - prefer-pytest (置信度: 0.85)
    
    请说 "确认删除" 或 "确认删除并删除本能" 或 "取消"

用户: 确认删除

AI: ✅ 技能 'testing-workflow' 已删除
    - 已删除源文件
    - 已删除 Cursor 同步
    - 已更新技能索引
    - 相关本能已保留
```

### 3.5 删除命令的识别机制

#### 问题背景

当用户说 "删除技能: testing-workflow" 时，Cursor（AI）如何知道：
1. 这是要删除**持续学习**生成的技能？
2. 应该调用哪个脚本来执行删除？
3. 还是 AI 可能直接物理删除文件？

#### 识别机制设计

采用 **Rules 规则指导** 的方式，让 AI 知道如何处理删除命令：

```markdown
# continuous-learning.mdc 规则文件中

## 删除技能命令

当用户说以下内容时，调用删除脚本：
- "删除技能: xxx"
- "删除学习到的技能 xxx"
- "移除技能 xxx"
- "delete skill xxx"

**执行方式**：
```bash
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py --delete-skill <skill-name>
```

**重要**：
- 不要直接使用 rm 或 Delete 工具删除文件
- 必须通过脚本删除，以确保同步文件和索引也被正确处理
```

#### 识别流程

```
用户: "删除技能: testing-workflow"
    │
    │ Cursor AI 读取 Rules
    ▼
┌─────────────────────────────────────────────────────────┐
│  continuous-learning.mdc 规则匹配                        │
│                                                         │
│  匹配到: "删除技能: xxx"                                 │
│  识别为: 持续学习技能删除命令                            │
│  执行方式: 调用 instinct.py --delete-skill              │
│                                                         │
└────────────────────────────┬────────────────────────────┘
                             │
                             │ AI 执行脚本
                             ▼
┌─────────────────────────────────────────────────────────┐
│  python3 instinct.py --delete-skill testing-workflow    │
│                                                         │
│  脚本执行：                                              │
│  1. 删除源文件                                          │
│  2. 删除 Cursor 同步                                    │
│  3. 更新索引                                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 风险和缓解措施

| 风险 | 描述 | 缓解措施 |
|------|------|---------|
| **AI 直接删除文件** | AI 可能使用 Delete 工具直接删除，导致同步文件和索引不一致 | 在规则中明确禁止直接删除 |
| **命令误识别** | AI 可能将其他删除命令误识别为技能删除 | 使用明确的命令格式，如 "删除技能:" |
| **规则未加载** | 如果规则文件未正确加载，AI 不知道如何处理 | 在 SKILL.md 中也说明删除方式 |
| **脚本执行失败** | 脚本可能因各种原因失败 | 脚本返回详细错误信息，AI 可以重试或提示用户 |

#### 规则文件中的删除指导

```markdown
# continuous-learning.mdc

## 技能管理命令

### 删除技能

**触发词**：
- "删除技能: <name>"
- "删除学习到的技能 <name>"
- "移除技能 <name>"

**执行方式**：
```bash
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py --delete-skill <name>
```

**禁止操作**：
- ❌ 不要使用 `rm -rf` 直接删除目录
- ❌ 不要使用 Delete 工具直接删除文件
- ❌ 不要手动编辑 skills-index.json

**原因**：
直接删除文件会导致：
1. Cursor 中的同步文件/链接未被删除
2. 技能索引未更新
3. 相关本能状态不一致

**正确做法**：
始终通过 `instinct.py --delete-skill` 脚本删除，脚本会：
1. 删除源文件
2. 删除 Cursor 同步
3. 更新索引
4. 可选删除相关本能
```

#### SKILL.md 中的删除说明

```markdown
# Continuous Learning Skill

...

## 用户命令

### 删除技能

当用户想删除学习到的技能时：

```bash
# 正确方式：通过脚本删除
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py --delete-skill <skill-name>

# 错误方式：直接删除文件（会导致不一致）
# rm -rf ~/.cursor/skills/evolved-<skill-name>  ❌
```
```

#### 双重保障机制

为了确保删除操作正确执行，采用双重保障：

1. **Rules 规则指导**：在规则文件中明确说明删除方式
2. **SKILL.md 说明**：在技能文件中也说明删除方式

```
用户: "删除技能: testing-workflow"
    │
    ├─→ 方式 1: AI 读取 Rules，调用脚本 ✅
    │
    └─→ 方式 2: AI 读取 SKILL.md，调用脚本 ✅
```

#### 如果 AI 直接删除了怎么办？

如果 AI 绕过脚本直接删除了文件，会导致以下问题：

| 问题 | 影响 | 修复方式 |
|------|------|---------|
| Cursor 同步未删除 | Cursor 仍然能看到技能 | 手动删除 `~/.cursor/skills/evolved-xxx` |
| 索引未更新 | 索引中仍有该技能记录 | 运行 `instinct.py --sync` 重建索引 |
| 相关本能状态不一致 | 本能仍指向已删除的技能 | 运行 `instinct.py --cleanup` 清理 |

**自动修复机制**：

```python
def sync_and_cleanup():
    """
    同步和清理机制
    
    在 --init 时自动运行，修复不一致状态
    """
    # 1. 检查 evolved/skills 中的实际技能
    actual_skills = list_actual_skills()
    
    # 2. 检查索引中的技能
    indexed_skills = list_indexed_skills()
    
    # 3. 检查 Cursor 中的同步
    cursor_skills = list_cursor_synced_skills()
    
    # 4. 修复不一致
    for skill in indexed_skills:
        if skill not in actual_skills:
            # 索引中有但实际不存在，清理索引
            remove_from_index(skill)
    
    for skill in cursor_skills:
        if skill not in actual_skills:
            # Cursor 中有但实际不存在，删除同步
            remove_cursor_sync(skill)
```

这个机制确保即使 AI 直接删除了文件，下次会话开始时也会自动修复不一致状态。

### 3.6 区分演化技能和其他技能

#### 问题背景

用户可能想删除的技能有两种：
1. **演化生成的技能**：由持续学习 Skill 自动生成的技能
2. **其他技能**：手动安装的技能，如 memory、behavior-prediction 等

如果用户说 "删除技能: memory"，持续学习的删除逻辑不应该处理这个请求。

#### 技能类型识别

| 技能类型 | 存放位置 | 命名特征 | 删除方式 |
|---------|---------|---------|---------|
| **演化技能** | `~/.cursor/skills/evolved-xxx/` | 以 `evolved-` 开头 | 通过 instinct.py 删除 |
| **手动技能** | `~/.cursor/skills/xxx/` | 无特殊前缀 | 用户手动删除或使用其他方式 |

#### 识别流程

```
用户: "删除技能: xxx"
    │
    │ AI 检查技能类型
    ▼
┌─────────────────────────────────────────────────────────┐
│  检查 1: 是否在演化技能索引中？                          │
│                                                         │
│  读取 continuous-learning-data/evolved/skills-index.json│
│  检查 skills 列表中是否有 name == "xxx"                 │
│                                                         │
└────────────────────────────┬────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│  是演化技能              │   │  不是演化技能            │
│                         │   │                         │
│  调用 instinct.py       │   │  提示用户：              │
│  --delete-skill xxx     │   │  "这不是演化生成的技能，  │
│                         │   │   请手动删除或使用其他   │
│                         │   │   方式"                 │
└─────────────────────────┘   └─────────────────────────┘
```

#### 规则文件中的类型检查

```markdown
# continuous-learning.mdc

## 删除技能命令

当用户说 "删除技能: xxx" 时：

### 步骤 1: 检查技能类型

首先检查是否是演化生成的技能：

```bash
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py --check-skill <name>
```

返回结果：
- `{"is_evolved": true, ...}` → 是演化技能，继续删除
- `{"is_evolved": false, ...}` → 不是演化技能，提示用户

### 步骤 2: 根据类型处理

**如果是演化技能**：
```bash
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py --delete-skill <name>
```

**如果不是演化技能**：
告诉用户：
"'xxx' 不是由持续学习生成的技能。如果你想删除它，可以：
1. 手动删除目录：rm -rf ~/.cursor/skills/xxx
2. 或者告诉我具体要删除哪个技能"
```

#### 脚本实现

```python
def check_skill(skill_name: str) -> dict:
    """
    检查技能是否是演化生成的
    
    Args:
        skill_name: 技能名称
    
    Returns:
        {
            "is_evolved": bool,
            "skill_name": str,
            "path": str (如果是演化技能),
            "suggestion": str (如果不是演化技能)
        }
    """
    # 1. 检查索引
    index = load_skills_index()
    for skill in index.get("skills", []):
        if skill["name"] == skill_name:
            return {
                "is_evolved": True,
                "skill_name": skill_name,
                "path": skill["path"],
                "cursor_path": skill["cursor_path"]
            }
    
    # 2. 检查是否存在于 Cursor skills 目录（但不是演化技能）
    cursor_path = Path.home() / ".cursor" / "skills" / skill_name
    if cursor_path.exists():
        return {
            "is_evolved": False,
            "skill_name": skill_name,
            "suggestion": f"'{skill_name}' 不是演化生成的技能。"
                         f"如果要删除，请手动执行: rm -rf {cursor_path}"
        }
    
    # 3. 技能不存在
    return {
        "is_evolved": False,
        "skill_name": skill_name,
        "suggestion": f"未找到名为 '{skill_name}' 的技能"
    }


def handle_delete_skill_command(skill_name: str) -> dict:
    """
    处理删除技能命令
    
    自动检查技能类型并执行相应操作
    """
    # 1. 检查技能类型
    check_result = check_skill(skill_name)
    
    if not check_result["is_evolved"]:
        # 不是演化技能，返回建议
        return {
            "status": "not_evolved",
            "message": check_result["suggestion"]
        }
    
    # 2. 是演化技能，执行删除
    return delete_evolved_skill(skill_name)
```

#### 用户交互示例

**示例 1: 删除演化技能**

```
用户: 删除技能: testing-workflow

AI: [检查技能类型...]
    'testing-workflow' 是演化生成的技能。
    
    即将删除以下内容：
    - 技能文件: evolved/skills/testing-workflow/
    - Cursor 同步: ~/.cursor/skills/evolved-testing-workflow/
    
    确认删除吗？

用户: 确认

AI: ✅ 技能 'testing-workflow' 已删除
```

**示例 2: 尝试删除非演化技能**

```
用户: 删除技能: memory

AI: [检查技能类型...]
    'memory' 不是由持续学习生成的技能，而是手动安装的技能。
    
    如果你确实想删除它，可以：
    1. 手动删除目录: rm -rf ~/.cursor/skills/memory
    2. 或者告诉我你想删除的具体内容
    
    注意：删除 memory 技能会导致记忆功能不可用。
```

**示例 3: 技能不存在**

```
用户: 删除技能: not-exist

AI: [检查技能类型...]
    未找到名为 'not-exist' 的技能。
    
    你可以说 "查看学习到的技能" 来查看所有演化生成的技能。
```

#### 命名约定

为了更容易区分演化技能和手动技能，采用以下命名约定：

| 技能类型 | 目录命名 | 示例 |
|---------|---------|------|
| **演化技能** | `evolved-<name>` | `evolved-testing-workflow` |
| **手动技能** | `<name>` | `memory`, `behavior-prediction` |

这样即使不查询索引，也可以通过目录名快速判断技能类型。

#### 安全措施总结

| 措施 | 说明 |
|------|------|
| **索引检查** | 只有在索引中的技能才被识别为演化技能 |
| **命名约定** | 演化技能以 `evolved-` 开头 |
| **类型提示** | 如果不是演化技能，明确告诉用户 |
| **手动删除指导** | 对于非演化技能，提供手动删除的命令 |

---

## 4. 触发机制

### 4.1 规则驱动（核心）

由于 Cursor 没有原生 Hook，采用 Rules 系统指导 AI 主动调用脚本：

```markdown
---
description: 持续学习 - 会话生命周期管理
globs: ["**/*"]
alwaysApply: true
---

# 持续学习规则

## 会话开始时
每次新会话开始时，调用初始化脚本：
```bash
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --init
```

## 会话过程中
在以下时机调用记录脚本：
- 完成文件创建/修改后
- 用户给出反馈/纠正后
- 完成一个功能点后

## 会话结束时
检测到结束信号或下次 --init 时自动保存。
```

### 4.2 触发可靠性

| 时机 | 触发方式 | 可靠性 |
|------|---------|--------|
| 会话开始 | 规则指导 AI 调用 `--init` | ~80-90% |
| 会话过程 | 规则指导 AI 调用 `--record` | ~50-70% |
| 会话结束 | 下次 `--init` 自动处理 | ~95% |

### 4.3 补偿机制

为了应对触发不可靠的问题，采用以下补偿机制：

1. **自动 Finalize**：每次 `--init` 时检查并保存上次未完成的会话
2. **批量记录**：不要求每次工具调用都记录，在关键节点批量记录
3. **AI 主动分析**：会话结束时，AI 主动分析并提取模式

---

## 5. 模式检测算法

### 5.1 用户纠正检测

```python
def detect_user_correction(observations: list) -> list:
    """
    检测用户纠正模式
    
    特征：
    1. AI 执行了某个操作
    2. 用户立即给出负面反馈或纠正
    3. AI 修改了之前的操作
    """
    corrections = []
    
    for i, obs in enumerate(observations):
        if obs.get("event") == "user_feedback":
            # 检查是否是纠正类型
            if is_correction_feedback(obs.get("content", "")):
                # 查找之前的 AI 操作
                prev_action = find_previous_action(observations, i)
                # 查找之后的修正操作
                next_action = find_next_action(observations, i)
                
                if prev_action and next_action:
                    corrections.append({
                        "original": prev_action,
                        "correction": obs,
                        "fixed": next_action
                    })
    
    return corrections
```

### 5.2 错误解决检测

```python
def detect_error_resolution(observations: list) -> list:
    """
    检测错误解决模式
    
    特征：
    1. 工具调用返回错误
    2. 后续操作解决了错误
    3. 相同错误类型被类似方式解决多次
    """
    resolutions = []
    
    for i, obs in enumerate(observations):
        if obs.get("event") == "tool_error":
            error_type = classify_error(obs.get("error", ""))
            # 查找解决方案
            solution = find_solution(observations, i, error_type)
            
            if solution:
                resolutions.append({
                    "error_type": error_type,
                    "error": obs,
                    "solution": solution
                })
    
    return resolutions
```

### 5.3 置信度计算

```python
def calculate_confidence(evidence_count: int, days_since_last: int) -> float:
    """
    计算本能的置信度
    
    基础置信度：
    - 1-2 次观察: 0.3 (试探性)
    - 3-5 次观察: 0.5 (中等)
    - 6-10 次观察: 0.7 (强)
    - 11+ 次观察: 0.85 (很强)
    
    时间衰减：
    - 每周衰减 0.02
    """
    # 基础置信度
    if evidence_count <= 2:
        base = 0.3
    elif evidence_count <= 5:
        base = 0.5
    elif evidence_count <= 10:
        base = 0.7
    else:
        base = 0.85
    
    # 时间衰减
    weeks = days_since_last / 7
    decay = 0.02 * weeks
    
    return max(0.1, base - decay)
```

---

## 6. 脚本接口设计

### 6.1 observe.py

```python
#!/usr/bin/env python3
"""
观察脚本 - 管理会话生命周期

用法：
  --init      会话开始时调用
  --record    记录动作
  --finalize  会话结束时调用
"""

def handle_init() -> dict:
    """
    会话开始时：
    1. 自动 finalize 上次未完成的会话
    2. 加载已学习的知识
    3. 返回 AI 可用的摘要和建议
    """
    pass

def handle_record(data: dict) -> dict:
    """
    记录动作：
    1. 追加到当前会话的观察记录
    2. 简单记录，不做复杂分析
    """
    pass

def handle_finalize(data: dict) -> dict:
    """
    会话结束时：
    1. 保存观察记录
    2. 触发模式分析
    3. 更新本能和技能
    """
    pass
```

### 6.2 analyze.py

```python
#!/usr/bin/env python3
"""
分析脚本 - 从观察记录中提取模式

用法：
  --session <session_id>  分析指定会话
  --recent <days>         分析最近 N 天的会话
  --all                   分析所有会话
"""

def analyze_session(session_id: str) -> dict:
    """分析单个会话，提取模式"""
    pass

def analyze_recent(days: int) -> dict:
    """分析最近 N 天的会话"""
    pass

def extract_patterns(observations: list) -> list:
    """从观察记录中提取模式"""
    pass
```

### 6.3 instinct.py

```python
#!/usr/bin/env python3
"""
本能管理脚本

用法：
  status                显示所有本能
  create <data>         创建新本能
  update <id> <data>    更新本能
  delete <id>           删除本能
  evolve                演化本能为技能
"""

def list_instincts() -> list:
    """列出所有本能"""
    pass

def create_instinct(data: dict) -> dict:
    """创建新本能"""
    pass

def update_instinct(instinct_id: str, data: dict) -> dict:
    """更新本能"""
    pass

def evolve_instincts() -> dict:
    """将相关本能演化为技能"""
    pass
```

---

## 7. 配置选项

### 7.1 默认配置 (default_config.json)

```json
{
  "version": "1.0",
  "enabled": true,
  "observation": {
    "enabled": true,
    "retention_days": 90,
    "max_file_size_mb": 10
  },
  "detection": {
    "enabled": true,
    "patterns": [
      "user_corrections",
      "error_resolutions",
      "tool_preferences",
      "project_conventions"
    ],
    "min_evidence_count": 2
  },
  "instincts": {
    "min_confidence": 0.3,
    "auto_apply_threshold": 0.7,
    "confidence_decay_rate": 0.02,
    "max_instincts": 100
  },
  "evolution": {
    "enabled": true,
    "cluster_threshold": 3,
    "auto_evolve": false
  }
}
```

### 7.2 配置说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enabled` | `true` | 总开关 |
| `observation.retention_days` | `90` | 观察记录保留天数 |
| `detection.min_evidence_count` | `2` | 最少证据数才创建本能 |
| `instincts.min_confidence` | `0.3` | 最低置信度 |
| `instincts.auto_apply_threshold` | `0.7` | 自动应用阈值 |
| `evolution.cluster_threshold` | `3` | 演化所需最少本能数 |

---

## 8. 规则安装机制

### 8.1 规则安装脚本 (setup_rule.py)

参考 behavior-prediction 和 memory skill 的实现，提供规则安装脚本：

```python
#!/usr/bin/env python3
"""
设置持续学习规则

为不同的 AI 助手生成持续学习规则文件。
"""

# 支持的操作
# - enable: 启用规则
# - disable: 禁用规则
# - update: 更新规则到最新版本
# - check: 检查规则状态

# 支持的 AI 助手类型
# - cursor: .cursor/rules/continuous-learning.mdc
# - claude: .claude/rules/continuous-learning.md
# - generic: .ai/rules/continuous-learning.md
```

### 8.2 用法

```bash
# 启用持续学习规则（项目级）
python3 ~/.cursor/skills/continuous-learning/scripts/setup_rule.py '{"action": "enable"}'

# 启用持续学习规则（全局）
python3 ~/.cursor/skills/continuous-learning/scripts/setup_rule.py '{"action": "enable", "location": "global"}'

# 禁用持续学习规则
python3 ~/.cursor/skills/continuous-learning/scripts/setup_rule.py '{"action": "disable"}'

# 更新规则到最新版本
python3 ~/.cursor/skills/continuous-learning/scripts/setup_rule.py '{"action": "update"}'

# 检查规则状态
python3 ~/.cursor/skills/continuous-learning/scripts/setup_rule.py '{"action": "check"}'

# 指定 AI 助手类型
python3 ~/.cursor/skills/continuous-learning/scripts/setup_rule.py '{"action": "enable", "assistant_type": "cursor"}'
```

### 8.3 规则文件位置

| AI 助手 | 规则目录 | 规则文件 |
|--------|---------|---------|
| Cursor | `.cursor/rules/` | `continuous-learning.mdc` |
| Claude | `.claude/rules/` | `continuous-learning.md` |
| Generic | `.ai/rules/` | `continuous-learning.md` |

### 8.4 安装流程

```
用户: 启用持续学习规则

AI: [执行 setup_rule.py '{"action": "enable"}']
    
    返回结果：
    {
      "success": true,
      "rule_file": "~/.cursor/rules/continuous-learning.mdc",
      "assistant_type": "cursor",
      "location": "project",
      "message": "持续学习规则已启用"
    }

AI 响应: ✅ 持续学习规则已启用！
         
         规则文件: ~/.cursor/rules/continuous-learning.mdc
         
         现在我会自动：
         - 会话开始时加载学习历史
         - 会话过程中记录关键动作
         - 会话结束时保存并分析模式
```

### 8.5 SKILL.md 中的安装说明

在 SKILL.md 中需要明确说明规则安装步骤：

```markdown
## 安装后提示

✅ **Continuous Learning Skill 安装成功！**

### 下一步：启用规则

说 **"启用持续学习规则"** 开始使用。

或者手动执行：
```bash
python3 ~/.cursor/skills/continuous-learning/scripts/setup_rule.py '{"action": "enable"}'
```

### 其他命令

| 命令 | 说明 |
|------|------|
| `启用持续学习规则` | 开启自动学习功能 |
| `禁用持续学习规则` | 关闭自动学习功能 |
| `更新持续学习规则` | 更新规则到最新版本 |
| `检查持续学习规则状态` | 检查规则是否已启用 |
```

---

## 9. 用户交互命令

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

---

## 9. 与其他 Skill 的集成

### 9.1 与 behavior-prediction 的集成

持续学习和行为预测可以共享部分数据：

```
共享数据：
- 会话记录（sessions/）
- 工作流程阶段识别

独立数据：
- 持续学习：本能、演化技能
- 行为预测：工作流程模式、预测数据
```

### 9.2 与 memory 的集成

持续学习可以利用 memory skill 的记忆数据：

```
利用方式：
- 从历史记忆中提取用户偏好
- 将学习到的知识作为记忆保存
```

---

## 10. 隐私说明

- 所有数据存储在本地
- 不上传任何信息到服务器
- 用户可以随时删除学习数据
- 本能文件不包含实际代码，只包含模式描述

---

## 11. 实现计划

### 第一阶段：基础框架

1. 创建目录结构
2. 实现 observe.py 基础功能
3. 实现规则文件
4. 实现自动 finalize 机制

### 第二阶段：模式检测

1. 实现用户纠正检测
2. 实现错误解决检测
3. 实现工具偏好检测
4. 实现置信度计算

### 第三阶段：知识生成

1. 实现本能创建和管理
2. 实现本能演化为技能
3. 实现技能文件生成

### 第四阶段：知识应用

1. 实现知识自动加载
2. 实现上下文注入
3. 实现 AI 行为调整

---

## 12. 风险和挑战

### 12.1 触发可靠性

**风险**：Rules 驱动的触发不如 Hook 可靠

**缓解措施**：
- 自动 finalize 机制
- 批量记录而非实时记录
- AI 主动分析补偿

### 12.2 模式检测准确性

**风险**：可能误判用户意图

**缓解措施**：
- 设置最低证据数阈值
- 置信度机制
- 用户可以删除错误的本能

### 12.3 知识过时

**风险**：学习到的知识可能过时

**缓解措施**：
- 时间衰减机制
- 用户可以手动更新
- 定期清理低置信度本能
