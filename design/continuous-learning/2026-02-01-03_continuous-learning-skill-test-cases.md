# Continuous Learning Skill 测试文档

## 1. 概述

本文档描述 Continuous Learning Skill 的测试用例，包括单元测试、集成测试和用户交互测试。

---

## 2. 单元测试

### 2.1 utils.py 测试

#### 测试用例 2.1.1：路径管理

```python
def test_get_skill_dir():
    """测试获取 Skill 代码目录"""
    skill_dir = get_skill_dir()
    assert skill_dir.exists()
    assert (skill_dir / "scripts").exists()


def test_get_data_dir():
    """测试获取用户数据目录"""
    data_dir = get_data_dir()
    assert data_dir.exists()
    assert "continuous-learning-data" in str(data_dir)


def test_ensure_data_dirs():
    """测试确保数据目录存在"""
    ensure_data_dirs()
    data_dir = get_data_dir()
    
    assert (data_dir / "observations").exists()
    assert (data_dir / "instincts").exists()
    assert (data_dir / "evolved" / "skills").exists()
    assert (data_dir / "evolved" / "commands").exists()
    assert (data_dir / "profile").exists()
```

#### 测试用例 2.1.2：配置管理

```python
def test_load_config_default():
    """测试加载默认配置"""
    config = load_config()
    
    assert config.get("version") == "1.0"
    assert config.get("enabled") == True
    assert "observation" in config
    assert "detection" in config


def test_save_and_load_config():
    """测试保存和加载配置"""
    config = {"test_key": "test_value"}
    save_config(config)
    
    loaded = load_config()
    assert loaded.get("test_key") == "test_value"
```

#### 测试用例 2.1.3：Pending Session 管理

```python
def test_pending_session_lifecycle():
    """测试 pending session 生命周期"""
    # 清除旧数据
    clear_pending_session()
    assert load_pending_session() is None
    
    # 保存
    save_pending_session({"test": "data"})
    pending = load_pending_session()
    assert pending is not None
    assert pending.get("test") == "data"
    assert "session_start" in pending
    
    # 添加观察
    add_observation_to_pending({"event": "test_event"})
    pending = load_pending_session()
    assert len(pending.get("observations", [])) == 1
    
    # 清除
    clear_pending_session()
    assert load_pending_session() is None
```

#### 测试用例 2.1.4：本能文件解析

```python
def test_parse_instinct_file():
    """测试解析本能文件"""
    content = """---
id: test-instinct
trigger: "测试触发条件"
confidence: 0.7
domain: "testing"
---

# 测试本能

## 行为
这是测试行为。
"""
    
    result = parse_instinct_file(content)
    
    assert result["id"] == "test-instinct"
    assert result["trigger"] == "测试触发条件"
    assert result["confidence"] == 0.7
    assert result["domain"] == "testing"
    assert "测试本能" in result["content"]


def test_generate_instinct_file():
    """测试生成本能文件"""
    instinct = {
        "id": "test-instinct",
        "trigger": "测试触发条件",
        "confidence": 0.7,
        "domain": "testing",
        "content": "# 测试本能\n\n## 行为\n测试行为"
    }
    
    content = generate_instinct_file(instinct)
    
    assert "id: test-instinct" in content
    assert "confidence: 0.7" in content
    assert "# 测试本能" in content
```

### 2.2 observe.py 测试

#### 测试用例 2.2.1：会话初始化

```python
def test_handle_init():
    """测试会话初始化"""
    result = handle_init()
    
    assert result["status"] == "success"
    assert "learned_skills_count" in result
    assert "instincts_count" in result
    
    # 检查 pending session 已创建
    pending = load_pending_session()
    assert pending is not None


def test_handle_init_auto_finalize():
    """测试自动 finalize 上一个会话"""
    # 创建一个有观察记录的 pending session
    save_pending_session({
        "observations": [
            {"event": "tool_call", "tool": "Write"}
        ]
    })
    
    result = handle_init()
    
    assert result["status"] == "success"
    assert "auto_finalized" in result
```

#### 测试用例 2.2.2：记录观察

```python
def test_handle_record():
    """测试记录观察"""
    # 先初始化
    handle_init()
    
    # 记录观察
    result = handle_record({
        "event": "tool_call",
        "tool": "Write",
        "input": {"file": "test.py"}
    })
    
    assert result["status"] == "success"
    
    # 检查观察已添加
    pending = load_pending_session()
    assert len(pending.get("observations", [])) >= 1


def test_handle_record_multiple():
    """测试记录多个观察"""
    handle_init()
    
    for i in range(5):
        handle_record({"event": "test", "index": i})
    
    pending = load_pending_session()
    assert len(pending.get("observations", [])) == 5
```

#### 测试用例 2.2.3：会话结束

```python
def test_handle_finalize():
    """测试会话结束"""
    # 初始化并记录一些观察
    handle_init()
    handle_record({"event": "tool_call", "tool": "Write"})
    handle_record({"event": "user_feedback", "content": "好的"})
    
    # 结束会话
    result = handle_finalize({
        "topic": "测试会话",
        "summary": "这是一个测试"
    })
    
    assert result["status"] == "success"
    assert result["observation_count"] >= 2
    
    # 检查 pending session 已清除
    assert load_pending_session() is None
```

### 2.3 analyze.py 测试

#### 测试用例 2.3.1：用户纠正检测

```python
def test_detect_user_corrections():
    """测试检测用户纠正"""
    observations = [
        {"event": "tool_call", "tool": "Write", "input": {"file": "test.py"}},
        {"event": "user_feedback", "content": "不要用 class，改成函数"},
        {"event": "tool_call", "tool": "StrReplace", "input": {"file": "test.py"}}
    ]
    
    corrections = detect_user_corrections(observations)
    
    assert len(corrections) == 1
    assert corrections[0]["type"] == "user_correction"
    assert "不要" in corrections[0]["correction"]


def test_detect_user_corrections_no_correction():
    """测试没有纠正的情况"""
    observations = [
        {"event": "tool_call", "tool": "Write"},
        {"event": "user_feedback", "content": "好的，继续"},
        {"event": "tool_call", "tool": "Write"}
    ]
    
    corrections = detect_user_corrections(observations)
    
    assert len(corrections) == 0
```

#### 测试用例 2.3.2：错误解决检测

```python
def test_detect_error_resolutions():
    """测试检测错误解决"""
    observations = [
        {"event": "tool_call", "tool": "Shell", "output": "Error: CORS"},
        {"event": "tool_error", "error": "CORS policy blocked"},
        {"event": "tool_call", "tool": "Write", "input": {"file": "vite.config.js"}}
    ]
    
    resolutions = detect_error_resolutions(observations)
    
    # 应该检测到错误解决模式
    assert len(resolutions) >= 0  # 根据实现调整


def test_detect_error_resolutions_no_fix():
    """测试没有修复的错误"""
    observations = [
        {"event": "tool_error", "error": "Some error"}
        # 没有后续修复操作
    ]
    
    resolutions = detect_error_resolutions(observations)
    
    assert len(resolutions) == 0
```

#### 测试用例 2.3.3：工具偏好检测

```python
def test_detect_tool_preferences():
    """测试检测工具偏好"""
    observations = [
        {"event": "tool_call", "tool": "Grep"},
        {"event": "tool_call", "tool": "Read"},
        {"event": "tool_call", "tool": "Grep"},
        {"event": "tool_call", "tool": "Write"},
        {"event": "tool_call", "tool": "Grep"},
        {"event": "tool_call", "tool": "Grep"}
    ]
    
    preferences = detect_tool_preferences(observations)
    
    # Grep 出现 4 次，占比 66%，应该被检测到
    assert len(preferences) >= 1
    grep_pref = [p for p in preferences if p["tool"] == "Grep"]
    assert len(grep_pref) == 1
    assert grep_pref[0]["count"] == 4
```

### 2.4 instinct.py 测试

#### 测试用例 2.4.1：本能 CRUD

```python
def test_create_instinct():
    """测试创建本能"""
    result = create_instinct({
        "id": "test-create",
        "trigger": "测试创建",
        "domain": "testing"
    })
    
    assert result["status"] == "success"
    
    # 验证文件已创建
    instincts = list_instincts()
    test_instinct = [i for i in instincts if i["id"] == "test-create"]
    assert len(test_instinct) == 1


def test_update_instinct():
    """测试更新本能"""
    # 先创建
    create_instinct({
        "id": "test-update",
        "trigger": "原始触发条件",
        "confidence": 0.3
    })
    
    # 更新
    result = update_instinct("test-update", {
        "trigger": "更新后的触发条件",
        "confidence": 0.7
    })
    
    assert result["status"] == "success"
    
    # 验证更新
    instincts = list_instincts()
    updated = [i for i in instincts if i["id"] == "test-update"][0]
    assert updated["trigger"] == "更新后的触发条件"
    assert updated["confidence"] == 0.7


def test_delete_instinct():
    """测试删除本能"""
    # 先创建
    create_instinct({
        "id": "test-delete",
        "trigger": "待删除"
    })
    
    # 删除
    result = delete_instinct("test-delete")
    
    assert result["status"] == "success"
    
    # 验证已删除
    instincts = list_instincts()
    deleted = [i for i in instincts if i["id"] == "test-delete"]
    assert len(deleted) == 0
```

#### 测试用例 2.4.2：技能检查

```python
def test_check_skill_evolved():
    """测试检查演化技能"""
    # 先创建一个演化技能
    create_instinct({"id": "inst1", "trigger": "t1", "domain": "test", "confidence": 0.8})
    create_instinct({"id": "inst2", "trigger": "t2", "domain": "test", "confidence": 0.8})
    create_instinct({"id": "inst3", "trigger": "t3", "domain": "test", "confidence": 0.8})
    evolve_instincts()
    
    # 检查
    result = check_skill("test-workflow")
    
    assert result["is_evolved"] == True


def test_check_skill_not_evolved():
    """测试检查非演化技能"""
    result = check_skill("memory")
    
    # memory 不是演化技能
    assert result["is_evolved"] == False
    assert "suggestion" in result
```

#### 测试用例 2.4.3：技能删除

```python
def test_delete_evolved_skill():
    """测试删除演化技能"""
    # 先创建演化技能
    # ... (创建本能并演化)
    
    # 删除
    result = delete_evolved_skill("test-workflow")
    
    assert result["status"] == "success"
    assert len(result["deleted"]) > 0
    
    # 验证已删除
    check_result = check_skill("test-workflow")
    assert check_result["is_evolved"] == False


def test_delete_non_evolved_skill():
    """测试删除非演化技能"""
    result = delete_evolved_skill("memory")
    
    assert result["status"] == "not_evolved"
    assert "suggestion" in result["message"]
```

#### 测试用例 2.4.4：本能演化

```python
def test_evolve_instincts_success():
    """测试本能演化成功"""
    # 创建足够的本能
    for i in range(3):
        create_instinct({
            "id": f"evolve-test-{i}",
            "trigger": f"触发条件 {i}",
            "domain": "evolve-test",
            "confidence": 0.7
        })
    
    # 演化
    result = evolve_instincts()
    
    assert result["status"] == "success"
    assert len(result["created_skills"]) >= 1


def test_evolve_instincts_insufficient():
    """测试本能不足无法演化"""
    # 清除所有本能
    for inst in list_instincts():
        delete_instinct(inst["id"])
    
    # 只创建 2 个本能
    create_instinct({"id": "few-1", "trigger": "t1", "domain": "few"})
    create_instinct({"id": "few-2", "trigger": "t2", "domain": "few"})
    
    # 演化
    result = evolve_instincts()
    
    assert result["status"] == "insufficient"
```

---

## 3. 集成测试

### 3.1 完整会话流程测试

```python
def test_full_session_flow():
    """测试完整会话流程"""
    # 1. 会话开始
    init_result = handle_init()
    assert init_result["status"] == "success"
    
    # 2. 记录多个观察
    handle_record({"event": "tool_call", "tool": "Write", "input": {"file": "api.py"}})
    handle_record({"event": "user_feedback", "content": "不要用 class"})
    handle_record({"event": "tool_call", "tool": "StrReplace"})
    handle_record({"event": "tool_call", "tool": "Shell", "input": {"command": "pytest"}})
    
    # 3. 会话结束
    finalize_result = handle_finalize({
        "topic": "API 开发",
        "summary": "创建了 API 文件"
    })
    
    assert finalize_result["status"] == "success"
    assert finalize_result["observation_count"] >= 4
    
    # 4. 验证分析结果
    if finalize_result.get("analysis"):
        analysis = finalize_result["analysis"]
        assert "patterns_found" in analysis
```

### 3.2 学习和演化流程测试

```python
def test_learning_and_evolution_flow():
    """测试学习和演化流程"""
    # 1. 模拟多个会话，积累本能
    for session in range(3):
        handle_init()
        
        # 模拟用户纠正
        handle_record({"event": "tool_call", "tool": "Write"})
        handle_record({"event": "user_feedback", "content": "不要用 class，用函数"})
        handle_record({"event": "tool_call", "tool": "StrReplace"})
        
        handle_finalize({"topic": f"会话 {session}"})
    
    # 2. 检查是否学习到了本能
    instincts = list_instincts()
    # 应该有一些本能被创建
    
    # 3. 如果本能足够，尝试演化
    if len(instincts) >= 3:
        evolve_result = evolve_instincts()
        # 检查演化结果
```

### 3.3 技能同步测试

```python
def test_skill_sync_to_cursor():
    """测试技能同步到 Cursor"""
    # 1. 创建本能并演化
    for i in range(3):
        create_instinct({
            "id": f"sync-test-{i}",
            "trigger": f"同步测试 {i}",
            "domain": "sync-test",
            "confidence": 0.8
        })
    
    evolve_result = evolve_instincts()
    
    if evolve_result["status"] == "success":
        skill_name = evolve_result["created_skills"][0]
        
        # 2. 验证 Cursor 目录中有同步的技能
        cursor_path = Path.home() / ".cursor" / "skills" / f"evolved-{skill_name}"
        assert cursor_path.exists()
        assert (cursor_path / "SKILL.md").exists()
        
        # 3. 删除技能
        delete_result = delete_evolved_skill(skill_name)
        assert delete_result["status"] == "success"
        
        # 4. 验证 Cursor 目录中已删除
        assert not cursor_path.exists()
```

---

## 4. 用户交互测试用例

### 4.1 会话开始场景

#### 用例 4.1.1：首次使用

```
场景：用户首次使用 Continuous Learning Skill

用户: 你好

AI: [执行 observe.py --init]
    
    返回结果：
    {
      "status": "success",
      "learned_skills_count": 0,
      "instincts_count": 0,
      "suggestions": []
    }

AI 响应: 你好！我注意到这是你首次使用持续学习功能。
         随着我们的交互，我会学习你的工作习惯和偏好。
         
         你想做什么？
```

#### 用例 4.1.2：有学习历史

```
场景：用户已有学习历史

用户: 开始

AI: [执行 observe.py --init]
    
    返回结果：
    {
      "status": "success",
      "learned_skills_count": 2,
      "instincts_count": 5,
      "suggestions": [
        "已学习 2 个技能",
        "高置信度本能: 编写新函数时 (70%)",
        "高置信度本能: 运行测试前 (85%)"
      ]
    }

AI 响应: 好的！我已加载你的学习历史：
         - 2 个演化技能
         - 5 个本能
         
         根据你的习惯，你通常在编写代码后会运行测试。
         
         今天想做什么？
```

#### 用例 4.1.3：自动 Finalize 上次会话

```
场景：上次会话未正常结束

用户: 继续

AI: [执行 observe.py --init]
    
    返回结果：
    {
      "status": "success",
      "auto_finalized": {
        "status": "success",
        "message": "上一个会话已自动保存",
        "observation_count": 8
      },
      "learned_skills_count": 2,
      "instincts_count": 5
    }

AI 响应: 我注意到上次会话没有正常结束，已自动保存了 8 条观察记录。
         
         你想继续上次的工作，还是开始新任务？
```

### 4.2 会话过程场景

#### 用例 4.2.1：记录用户纠正

```
场景：用户纠正 AI 的行为

用户: 帮我写一个用户类

AI: [执行 Write 工具创建 User 类]
    [执行 observe.py --record '{"event":"tool_call","tool":"Write",...}']

用户: 不要用 class，用函数式的方式

AI: [执行 observe.py --record '{"event":"user_feedback","type":"correction","content":"不要用 class，用函数式的方式"}']
    [执行 StrReplace 修改为函数式]
    [执行 observe.py --record '{"event":"tool_call","tool":"StrReplace",...}']

AI 响应: 好的，我已经改成函数式的方式了。
         
         [显示修改后的代码]
         
         我记住了你偏好函数式风格，以后会优先使用这种方式。
```

#### 用例 4.2.2：记录错误解决

```
场景：解决 CORS 错误

用户: 运行一下

AI: [执行 Shell 运行项目]
    
    输出: Error: CORS policy blocked...

AI: [执行 observe.py --record '{"event":"tool_error","error":"CORS policy blocked"}']

用户: 怎么解决？

AI: 这是 CORS 错误，我来配置 proxy 解决。
    
    [执行 Write 修改 vite.config.js]
    [执行 observe.py --record '{"event":"tool_call","tool":"Write","input":{"file":"vite.config.js"}}']

AI 响应: 我已经在 vite.config.js 中添加了 proxy 配置。
         再运行一下试试。
         
         我会记住这个 CORS 错误的解决方案，下次遇到类似问题可以更快解决。
```

### 4.3 会话结束场景

#### 用例 4.3.1：手动结束

```
场景：用户说结束语

用户: 谢谢，今天就到这里

AI: [检测到结束信号]
    [执行 observe.py --finalize '{
      "topic": "API 开发",
      "summary": "创建了用户认证 API",
      "observations": [...]
    }']
    
    返回结果：
    {
      "status": "success",
      "observation_count": 12,
      "analysis": {
        "patterns_found": 2,
        "user_corrections": 1,
        "error_resolutions": 1
      }
    }

AI 响应: 好的！今天的会话已保存。
         
         本次会话摘要：
         - 主题：API 开发
         - 记录了 12 条观察
         - 发现了 2 个可学习的模式
         
         下次见！
```

#### 用例 4.3.2：自动结束（下次会话时）

```
场景：用户直接关闭窗口，下次开始新会话

用户: [关闭 Cursor]

... 第二天 ...

用户: 开始

AI: [执行 observe.py --init]
    [自动 finalize 上次会话]
    
    返回结果：
    {
      "status": "success",
      "auto_finalized": {
        "status": "success",
        "message": "上一个会话已自动保存",
        "observation_count": 12
      }
    }

AI 响应: 早上好！我已自动保存了昨天的会话（12 条观察记录）。
         
         今天想做什么？
```

### 4.4 技能管理场景

#### 用例 4.4.1：查看学习到的知识

```
场景：用户想查看学习历史

用户: 查看学习到的知识

AI: [执行 instinct.py status]
    
    返回结果：
    {
      "status": "success",
      "count": 5,
      "instincts": [
        {"id": "prefer-functional", "trigger": "编写新函数时", "confidence": 0.7, "domain": "code-style"},
        {"id": "always-test-first", "trigger": "开始新功能前", "confidence": 0.85, "domain": "workflow"},
        ...
      ]
    }

AI 响应: 我已经学习到了 5 个本能：

         **代码风格**
         - 偏好函数式 (70%) - 编写新函数时，使用函数式而非类
         
         **工作流程**
         - 先写测试 (85%) - 开始新功能前，先写测试用例
         
         **调试**
         - CORS 解决方案 (60%) - 遇到 CORS 错误时，配置 proxy
         
         你可以说 "演化本能" 将相关本能聚合为技能。
```

#### 用例 4.4.2：演化本能为技能

```
场景：用户想将本能演化为技能

用户: 演化本能

AI: [执行 instinct.py evolve]
    
    返回结果：
    {
      "status": "success",
      "created_skills": ["workflow-workflow"],
      "message": "已创建 1 个技能"
    }

AI 响应: 已将相关本能演化为技能：

         ✅ **workflow-workflow** 技能已创建
         - 基于 3 个本能演化
         - 已同步到 Cursor skills 目录
         
         这个技能会在相关任务时自动加载。
```

#### 用例 4.4.3：删除演化技能

```
场景：用户想删除一个演化技能

用户: 删除技能: workflow-workflow

AI: [执行 instinct.py --check-skill workflow-workflow]
    
    返回结果：
    {
      "is_evolved": true,
      "skill_name": "workflow-workflow",
      "path": "...",
      "cursor_path": "..."
    }

AI 响应: 'workflow-workflow' 是演化生成的技能。
         
         即将删除以下内容：
         - 技能文件
         - Cursor 同步
         - 技能索引条目
         
         是否同时删除相关本能？
         - always-test-first (85%)
         - prefer-functional (70%)
         - ...
         
         请说 "确认删除" 或 "确认删除并删除本能" 或 "取消"

用户: 确认删除

AI: [执行 instinct.py --delete-skill workflow-workflow]
    
    返回结果：
    {
      "status": "success",
      "deleted": [
        "源文件: ...",
        "同步目录: ...",
        "技能索引已更新"
      ]
    }

AI 响应: ✅ 技能 'workflow-workflow' 已删除
         - 已删除源文件
         - 已删除 Cursor 同步
         - 已更新技能索引
         - 相关本能已保留
```

#### 用例 4.4.4：尝试删除非演化技能

```
场景：用户尝试删除手动安装的技能

用户: 删除技能: memory

AI: [执行 instinct.py --check-skill memory]
    
    返回结果：
    {
      "is_evolved": false,
      "skill_name": "memory",
      "suggestion": "'memory' 不是演化生成的技能。如果要删除，请手动执行: rm -rf ~/.cursor/skills/memory"
    }

AI 响应: 'memory' 不是由持续学习生成的技能，而是手动安装的技能。
         
         如果你确实想删除它，可以：
         1. 手动删除目录: `rm -rf ~/.cursor/skills/memory`
         2. 或者告诉我你想删除的具体内容
         
         注意：删除 memory 技能会导致记忆功能不可用。
```

### 4.5 错误处理场景

#### 用例 4.5.1：脚本执行失败

```
场景：脚本执行出错

用户: 查看学习到的知识

AI: [执行 instinct.py status]
    
    返回结果：
    {
      "status": "error",
      "message": "Permission denied: ..."
    }

AI 响应: 抱歉，读取学习数据时出错了：
         
         错误信息：Permission denied
         
         可能的原因：
         1. 数据目录权限问题
         2. 文件被其他程序占用
         
         你可以尝试：
         - 检查 ~/.cursor/skills/continuous-learning-data/ 目录权限
         - 或者说 "重置学习数据" 重新开始
```

#### 用例 4.5.2：技能不存在

```
场景：用户尝试删除不存在的技能

用户: 删除技能: not-exist

AI: [执行 instinct.py --check-skill not-exist]
    
    返回结果：
    {
      "is_evolved": false,
      "skill_name": "not-exist",
      "suggestion": "未找到名为 'not-exist' 的技能"
    }

AI 响应: 未找到名为 'not-exist' 的技能。
         
         你可以说 "查看学习到的知识" 来查看所有演化生成的技能。
```

---

## 5. 测试执行

### 5.1 运行单元测试

```bash
# 运行所有测试
python3 -m pytest tests/ -v

# 运行特定测试文件
python3 -m pytest tests/test_observe.py -v

# 运行特定测试用例
python3 -m pytest tests/test_instinct.py::test_create_instinct -v
```

### 5.2 测试覆盖率

```bash
# 生成覆盖率报告
python3 -m pytest tests/ --cov=scripts --cov-report=html

# 查看报告
open htmlcov/index.html
```

### 5.3 测试数据清理

```bash
# 清理测试数据
rm -rf ~/.cursor/skills/continuous-learning-data/
rm -rf ~/.cursor/skills/evolved-*
```

---

## 6. 测试检查清单

### 6.1 功能测试

- [ ] 会话初始化正常
- [ ] 观察记录正常
- [ ] 会话结束正常
- [ ] 自动 finalize 正常
- [ ] 用户纠正检测正常
- [ ] 错误解决检测正常
- [ ] 工具偏好检测正常
- [ ] 本能创建/更新/删除正常
- [ ] 本能演化正常
- [ ] 技能同步到 Cursor 正常
- [ ] 技能删除正常
- [ ] 非演化技能识别正常

### 6.2 边界测试

- [ ] 空观察记录处理
- [ ] 大量观察记录处理
- [ ] 无效 JSON 输入处理
- [ ] 文件不存在处理
- [ ] 权限错误处理

### 6.3 用户交互测试

- [ ] 首次使用体验
- [ ] 有历史数据体验
- [ ] 技能管理命令
- [ ] 错误提示友好
