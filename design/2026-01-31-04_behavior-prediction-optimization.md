# 行为预测 Skill 优化方案

> **版本**: v1.1.0
> **创建日期**: 2026-01-31
> **更新日期**: 2026-01-31
> **问题**: 
> 1. 每次工具调用后都需要额外 Shell 调用来记录，影响效率
> 2. 动作分类太粗，缺少上下文信息，模式复用价值有限

## 一、问题分析

### 1.1 当前方案的问题

**现状**：
- 规则文件要求 AI 在**每次工具调用后**执行 `record_action.py` 记录
- 这意味着每个工具调用都需要额外的 Shell 调用
- 一次会话可能有 20-50 次工具调用，就需要 20-50 次额外的记录调用

**问题**：
1. **效率低下**：每次记录都是一次 Shell 调用，增加延迟
2. **干扰用户**：用户会看到大量记录操作的确认提示
3. **AI 负担**：AI 需要在每次工具调用后额外执行记录
4. **容易遗漏**：AI 可能专注于任务而忘记记录

### 1.2 根本原因

Cursor 的 AI 工具调用机制是**同步**的，没有提供：
- 工具调用后的钩子（hook）机制
- 批量执行工具的能力
- 后台静默执行的能力

## 二、优化方案

### 2.1 方案一：会话结束时批量记录（推荐）

**核心思想**：不在每次工具调用后记录，而是在会话结束时批量记录整个会话的所有动作。

**实现方式**：

1. **AI 在内存中维护动作列表**
   - 每次工具调用后，AI 在回复中记录动作信息（不执行 Shell）
   - 动作信息暂存在 AI 的上下文中

2. **会话结束时批量提交**
   - 当用户说"结束"、"再见"或长时间无响应时
   - AI 一次性调用 `batch_record_actions.py` 提交所有动作

**新增脚本**：`batch_record_actions.py`

```python
#!/usr/bin/env python3
"""
批量记录动作
用于会话结束时一次性记录所有动作
"""

import json
import sys
from datetime import datetime
from utils import get_data_dir, ensure_dir

def batch_record_actions(actions_json: str) -> dict:
    """
    批量记录动作
    
    Args:
        actions_json: JSON 格式的动作列表
        
    Returns:
        记录结果
    """
    try:
        actions = json.loads(actions_json)
        if not isinstance(actions, list):
            return {"status": "error", "message": "actions 必须是数组"}
        
        if len(actions) == 0:
            return {"status": "success", "message": "无动作需要记录", "count": 0}
        
        # 获取数据目录
        data_dir = get_data_dir()
        actions_dir = data_dir / "actions"
        ensure_dir(actions_dir)
        
        # 按日期分组
        actions_by_date = {}
        for action in actions:
            date = action.get("timestamp", "")[:10]  # 提取日期部分
            if date not in actions_by_date:
                actions_by_date[date] = []
            actions_by_date[date].append(action)
        
        # 写入各日期文件
        total_count = 0
        for date, date_actions in actions_by_date.items():
            file_path = actions_dir / f"{date}.json"
            
            # 读取现有数据
            existing_data = {"date": date, "actions": []}
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # 生成 ID 并追加
            start_id = len(existing_data["actions"]) + 1
            for i, action in enumerate(date_actions):
                action["id"] = f"{date}-{start_id + i:03d}"
                existing_data["actions"].append(action)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            total_count += len(date_actions)
        
        # 更新转移矩阵
        update_transition_matrix(actions)
        
        return {
            "status": "success",
            "message": f"成功记录 {total_count} 个动作",
            "count": total_count
        }
        
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"JSON 解析错误: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def update_transition_matrix(actions: list):
    """更新转移矩阵"""
    if len(actions) < 2:
        return
    
    data_dir = get_data_dir()
    matrix_file = data_dir / "patterns" / "transition_matrix.json"
    ensure_dir(matrix_file.parent)
    
    # 读取现有矩阵
    matrix = {}
    if matrix_file.exists():
        with open(matrix_file, 'r', encoding='utf-8') as f:
            matrix = json.load(f)
    
    # 更新转移计数
    for i in range(len(actions) - 1):
        from_type = actions[i].get("type", "unknown")
        to_type = actions[i + 1].get("type", "unknown")
        
        if from_type not in matrix:
            matrix[from_type] = {}
        if to_type not in matrix[from_type]:
            matrix[from_type][to_type] = {"count": 0}
        
        matrix[from_type][to_type]["count"] += 1
    
    # 计算概率
    for from_type, transitions in matrix.items():
        total = sum(t["count"] for t in transitions.values())
        for to_type, data in transitions.items():
            data["probability"] = round(data["count"] / total, 3) if total > 0 else 0
    
    # 保存
    with open(matrix_file, 'w', encoding='utf-8') as f:
        json.dump(matrix, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "缺少 actions 参数"}))
        sys.exit(1)
    
    result = batch_record_actions(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

**规则文件更新**：

```markdown
# Behavior Prediction Skill 自动行为记录规则（优化版）

## 记录方式：会话结束时批量记录

### 1. 会话中：内存暂存

在会话过程中，AI 在内部维护一个动作列表，不执行 Shell 调用：

```
内部动作列表 = [
  { type: "create_file", tool: "Write", timestamp: "...", details: {...} },
  { type: "edit_file", tool: "StrReplace", timestamp: "...", details: {...} },
  ...
]
```

### 2. 会话结束：批量提交

当检测到以下信号时，批量提交所有动作：

**结束信号**：
- 用户说"结束"、"再见"、"完成了"、"谢谢"
- 用户说"提交行为记录"
- 会话即将结束

**执行命令**：
```bash
python3 /path/to/batch_record_actions.py '[
  {"type": "create_file", "tool": "Write", "timestamp": "...", "details": {...}},
  {"type": "edit_file", "tool": "StrReplace", "timestamp": "...", "details": {...}}
]'
```

### 3. 动作分类（AI 在内存中分类）

| 工具 | 动作类型 | 记录内容 |
|------|----------|----------|
| Write（新文件） | create_file | file_path |
| Write/StrReplace | edit_file | file_path |
| Delete | delete_file | file_path |
| Read | read_file | file_path |
| Shell | 根据命令分类 | command, exit_code |
| Grep/Glob | search_code/search_file | pattern |
```

**优点**：
- 只需要 1 次 Shell 调用（会话结束时）
- 不干扰用户的正常操作
- AI 不需要频繁执行记录脚本

**缺点**：
- 如果会话异常中断，可能丢失记录
- AI 需要在上下文中维护动作列表

---

### 2.2 方案二：定时批量记录

**核心思想**：每隔 N 次工具调用，批量记录一次。

**实现方式**：

1. AI 在内存中累积动作
2. 每累积 10 个动作，执行一次批量记录
3. 会话结束时记录剩余动作

**规则示例**：

```markdown
## 记录策略

1. 每 10 次工具调用后，批量记录一次
2. 会话结束时，记录剩余动作
3. 记录时使用 batch_record_actions.py
```

**优点**：
- 减少 Shell 调用次数（从 N 次减少到 N/10 次）
- 即使会话中断，最多丢失 10 条记录

**缺点**：
- 仍需要多次 Shell 调用
- 需要 AI 计数

---

### 2.3 方案三：后台异步记录（理想方案，但 Cursor 不支持）

**核心思想**：工具调用后，后台异步执行记录，不阻塞主流程。

**为什么不可行**：
- Cursor 的 Shell 工具是同步的
- 没有后台执行机制
- 无法实现真正的异步

---

### 2.4 方案四：MCP 服务器记录（高级方案）

**核心思想**：创建一个 MCP 服务器，AI 通过 MCP 调用记录动作，MCP 服务器在后台批量处理。

**实现方式**：

1. 创建 `behavior-recorder` MCP 服务器
2. 提供 `record_action` 工具
3. MCP 服务器内部批量处理，定时写入文件

**MCP 服务器示例**：

```javascript
// behavior-recorder-mcp/index.js
const { Server } = require("@modelcontextprotocol/sdk/server/index.js");

class BehaviorRecorderServer {
  constructor() {
    this.pendingActions = [];
    this.flushInterval = setInterval(() => this.flush(), 30000); // 30秒刷新一次
  }

  async recordAction(action) {
    this.pendingActions.push({
      ...action,
      timestamp: new Date().toISOString()
    });
    
    // 累积超过 20 条时立即刷新
    if (this.pendingActions.length >= 20) {
      await this.flush();
    }
    
    return { success: true, queued: this.pendingActions.length };
  }

  async flush() {
    if (this.pendingActions.length === 0) return;
    
    // 批量写入文件
    const actions = [...this.pendingActions];
    this.pendingActions = [];
    
    // ... 写入逻辑
  }
}
```

**优点**：
- 真正的异步记录
- 不阻塞 AI 操作
- 自动批量处理

**缺点**：
- 需要额外配置 MCP 服务器
- 增加系统复杂度

---

## 三、推荐方案

### 3.1 短期方案：会话结束时批量记录（方案一）

**适用场景**：大多数情况

**实现步骤**：

1. 创建 `batch_record_actions.py` 脚本
2. 更新规则文件，指导 AI 在会话结束时批量记录
3. AI 在内存中维护动作列表

### 3.2 长期方案：MCP 服务器（方案四）

**适用场景**：需要精确记录、不能丢失数据

**实现步骤**：

1. 创建 `behavior-recorder` MCP 服务器
2. 配置 Cursor 使用该 MCP 服务器
3. AI 通过 MCP 调用记录动作

---

## 四、规则文件更新

### 4.1 更新后的规则文件

```markdown
# Behavior Prediction Skill 自动行为记录规则（优化版）

## 功能概述

该规则使 AI 助手能够：
1. **高效记录**用户在 AI 助手中执行的动作（会话结束时批量记录）
2. **学习模式**：分析行为序列，发现 A → B 的关联模式
3. **智能预测**：当用户执行动作 A 时，预测并建议动作 B

## 一、行为记录（优化版：批量记录）

### 1.1 记录策略

**不再**在每次工具调用后立即记录，而是：

1. **会话中**：AI 在内部维护动作列表（不执行 Shell）
2. **会话结束时**：一次性批量记录所有动作

### 1.2 内存中维护动作列表

每次执行工具调用后，AI 在内部记录动作信息：

```
// AI 内部维护的动作列表（不输出给用户）
session_actions = [
  { type: "create_file", tool: "Write", timestamp: "ISO8601", details: { file_path: "..." } },
  { type: "edit_file", tool: "StrReplace", timestamp: "ISO8601", details: { file_path: "..." } },
  ...
]
```

### 1.3 会话结束时批量提交

当检测到以下信号时，执行批量记录：

**结束信号**：
- 用户说"结束"、"再见"、"完成了"、"谢谢"、"好的"
- 用户说"提交行为记录"
- 用户长时间无响应（超过 5 分钟）

**执行命令**：
```bash
python3 /path/to/batch_record_actions.py '[动作列表JSON]'
```

### 1.4 动作分类

| 工具 | 动作类型 | 记录内容 |
|------|----------|----------|
| Write（新文件） | create_file | file_path |
| Write/StrReplace | edit_file | file_path |
| Delete | delete_file | file_path |
| Read | read_file | file_path |
| Shell（测试） | run_test | command |
| Shell（构建） | run_build | command |
| Shell（Git） | git_* | command |
| Shell（其他） | shell_command | command |
| Grep | search_code | pattern |
| Glob | search_file | pattern |

## 二、智能预测

（保持不变）

## 三、用户命令

| 命令 | 效果 |
|------|------|
| `查看我的行为模式` | 显示学习到的行为模式 |
| `预测下一步` | 手动触发预测 |
| `查看行为统计` | 显示统计数据概览 |
| `提交行为记录` | 手动触发批量记录 |

## 四、注意事项

- 会话中不执行记录 Shell 调用，提高效率
- 会话结束时批量记录，减少干扰
- 如果会话异常中断，可能丢失本次会话的记录
```

---

## 五、实施计划

### Phase 1：创建批量记录脚本

1. 创建 `scripts/batch_record_actions.py`
2. 测试批量记录功能
3. 更新 `get_statistics.py` 支持新的数据格式

### Phase 2：更新规则文件

1. 更新 `.cursor/rules/behavior-prediction-auto-record.mdc`
2. 添加会话结束检测逻辑
3. 测试新的记录流程

### Phase 3：（可选）MCP 服务器

1. 创建 `behavior-recorder` MCP 服务器
2. 配置 Cursor 使用 MCP 服务器
3. 迁移到 MCP 方案

---

## 六、上下文信息优化

### 6.1 问题：动作分类太粗

**当前记录的模式**：
```
create_file → create_file → create_file  (置信度: 100%, 但无意义)
```

**问题**：
- 只记录了动作类型（`create_file`），没有更多信息
- 无法区分"创建设计文档"和"创建代码文件"
- 模式太通用，无法提供有价值的预测

### 6.2 解决方案：添加上下文信息

在记录动作时，添加 `context` 字段，包含更丰富的信息。

#### 6.2.1 文件相关上下文

| 字段 | 说明 | 示例 |
|------|------|------|
| `file_type` | 文件扩展名 | `.py`, `.vue`, `.md`, `.json` |
| `file_category` | 文件分类 | `source_code`, `test`, `config`, `doc` |
| `file_path_pattern` | 文件路径模式 | `tests/`, `src/`, `design/` |
| `file_purpose` | 文件用途 | `api`, `component`, `store`, `schema` |

**示例**：
```json
{
  "type": "create_file",
  "tool": "Write",
  "details": {
    "file_path": "design/2026-01-31_xxx.md"
  },
  "context": {
    "file_type": ".md",
    "file_category": "doc",
    "file_path_pattern": "design/",
    "file_purpose": "design_doc"
  }
}
```

#### 6.2.2 项目相关上下文

| 字段 | 说明 | 示例 |
|------|------|------|
| `project_type` | 项目类型 | `skill`, `uniapp`, `python`, `java` |
| `project_name` | 项目名称 | `skillix-hub`, `tt-paikebao-mp` |
| `current_module` | 当前模块 | `behavior-prediction`, `memory` |

**示例**：
```json
{
  "type": "create_file",
  "context": {
    "project_type": "skill",
    "project_name": "skillix-hub",
    "current_module": "uniapp-mp-generator"
  }
}
```

#### 6.2.3 任务相关上下文

| 字段 | 说明 | 示例 |
|------|------|------|
| `task_type` | 任务类型 | `feature`, `bugfix`, `refactor`, `doc` |
| `task_stage` | 任务阶段 | `design`, `implement`, `test`, `deploy` |
| `user_intent` | 用户意图 | `create_skill`, `fix_bug`, `add_feature` |

**示例**：
```json
{
  "type": "create_file",
  "context": {
    "task_type": "feature",
    "task_stage": "design",
    "user_intent": "create_skill"
  }
}
```

#### 6.2.4 命令相关上下文（Shell 命令）

| 字段 | 说明 | 示例 |
|------|------|------|
| `command_type` | 命令类型 | `test`, `build`, `install`, `git` |
| `target_file` | 目标文件 | `tests/test_xxx.py` |
| `exit_code` | 退出码 | `0`, `1`, `127` |

**示例**：
```json
{
  "type": "run_test",
  "details": {
    "command": "pytest tests/"
  },
  "context": {
    "command_type": "test",
    "target_file": "tests/",
    "exit_code": 0
  }
}
```

### 6.3 改进后的模式识别

**无上下文（当前）**：
```
create_file → create_file  (置信度: 100%, 无意义)
```

**有上下文（改进后）**：
```
create_file[design_doc] → create_file[implementation_doc]  (置信度: 90%)
create_file[api] → create_file[test]  (置信度: 85%)
edit_file[.py] → run_test[pytest]  (置信度: 80%)
create_file[component] → edit_file[route]  (置信度: 75%)
```

### 6.4 上下文自动推断

AI 可以根据文件路径自动推断上下文：

```python
def infer_context(file_path: str) -> dict:
    """根据文件路径推断上下文"""
    context = {}
    
    # 文件类型
    ext = Path(file_path).suffix
    context["file_type"] = ext
    
    # 文件分类
    if ext in [".py", ".js", ".ts", ".vue", ".java"]:
        context["file_category"] = "source_code"
    elif ext in [".md", ".txt", ".rst"]:
        context["file_category"] = "doc"
    elif ext in [".json", ".yaml", ".yml", ".toml"]:
        context["file_category"] = "config"
    
    # 路径模式
    if "test" in file_path.lower():
        context["file_path_pattern"] = "tests/"
        context["file_purpose"] = "test"
    elif "design" in file_path.lower():
        context["file_path_pattern"] = "design/"
        context["file_purpose"] = "design_doc"
    elif "api" in file_path.lower():
        context["file_path_pattern"] = "api/"
        context["file_purpose"] = "api"
    elif "component" in file_path.lower():
        context["file_path_pattern"] = "components/"
        context["file_purpose"] = "component"
    elif "store" in file_path.lower():
        context["file_path_pattern"] = "stores/"
        context["file_purpose"] = "store"
    elif "template" in file_path.lower():
        context["file_path_pattern"] = "templates/"
        context["file_purpose"] = "template"
    
    return context
```

### 6.5 更新后的数据结构

**动作记录格式**：
```json
{
  "id": "2026-01-31-001",
  "type": "create_file",
  "tool": "Write",
  "timestamp": "2026-01-31T10:00:00+08:00",
  "details": {
    "file_path": "design/2026-01-31_xxx.md"
  },
  "context": {
    "file_type": ".md",
    "file_category": "doc",
    "file_path_pattern": "design/",
    "file_purpose": "design_doc",
    "project_type": "skill",
    "task_stage": "design"
  }
}
```

**转移矩阵格式**（支持上下文）：
```json
{
  "create_file": {
    "create_file": {
      "count": 10,
      "probability": 0.5,
      "by_context": {
        "design_doc→implementation_doc": { "count": 5, "probability": 0.9 },
        "api→test": { "count": 3, "probability": 0.85 },
        "component→component": { "count": 2, "probability": 0.6 }
      }
    }
  }
}
```

### 6.6 实施步骤

#### Phase 1：更新记录脚本

1. 修改 `record_action.py`，支持 `context` 参数
2. 添加 `infer_context()` 函数自动推断上下文
3. 更新数据存储格式

#### Phase 2：更新统计脚本

1. 修改 `get_statistics.py`，支持按上下文分组统计
2. 添加 `by_context` 字段到转移矩阵
3. 更新预测逻辑，考虑上下文

#### Phase 3：更新规则文件

1. 更新规则，指导 AI 记录上下文信息
2. 添加上下文推断逻辑说明

---

## 七、总结

### 7.1 效率优化

| 方案 | Shell 调用次数 | 复杂度 | 推荐 |
|------|---------------|--------|------|
| 当前方案（每次记录） | N 次 | 低 | ❌ |
| 方案一（会话结束批量） | 1 次 | 低 | ✅ 短期 |
| 方案二（定时批量） | N/10 次 | 中 | ⚠️ |
| 方案四（MCP 服务器） | 0 次（异步） | 高 | ✅ 长期 |

### 7.2 模式质量优化

| 优化项 | 当前 | 改进后 |
|--------|------|--------|
| 动作分类 | 粗粒度（`create_file`） | 细粒度（`create_file[design_doc]`） |
| 上下文信息 | 无 | 文件类型、分类、用途、项目类型等 |
| 模式价值 | 低（太通用） | 高（可预测具体场景） |
| 预测准确度 | 低 | 高 |

### 7.3 推荐实施顺序

1. **Phase 1**：实现批量记录（解决效率问题）
2. **Phase 2**：添加上下文信息（提高模式质量）
3. **Phase 3**：（可选）MCP 服务器（终极方案）
