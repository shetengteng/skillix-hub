# Standalone Memory Skill 测试报告

> 时间: 2026-02-19 17:26:06
> 结果: FAILED
> 耗时: 212.739s

## 套件汇总

| 套件 | 状态 | 总数 | 通过 | 失败 | 跳过 |
|---|---|---:|---:|---:|---:|
| modern (unittest) | FAILED | 16 | 14 | 2 | 0 |
| legacy (migrated) | PASSED | 155 | 155 | 0 | 0 |

## Modern 按模块结果

### test_config_entrypoints

| 用例 | 状态 |
|---|---|
| `test_init_creates_config_json` | PASS |
| `test_manage_config_invalid_key_returns_error` | PASS |
| `test_manage_config_set_and_get_roundtrip` | PASS |
| `test_project_facts_limit_should_affect_load_memory` | FAIL |
| `test_reset_all_should_work` | FAIL |

### test_e2e_flow

| 用例 | 状态 |
|---|---|
| `test_saved_daily_fact_loaded_by_session_start` | PASS |
| `test_session_end_sync_makes_new_fact_searchable` | PASS |

### test_hook_contracts

| 用例 | 状态 |
|---|---|
| `test_flush_memory_returns_user_message_contract` | PASS |
| `test_load_memory_returns_additional_context_json` | PASS |
| `test_prompt_session_save_completed_returns_followup` | PASS |
| `test_prompt_session_save_non_completed_returns_empty_json` | PASS |

### test_install_path_logic

| 用例 | 状态 |
|---|---|
| `test_global_relative_path_depends_on_project_depth` | PASS |
| `test_local_mode_relative_path_is_stable` | PASS |

### test_unit_behavior

| 用例 | 状态 |
|---|---|
| `test_partial_window_prefers_latest_entries` | PASS |
| `test_save_fact_cli_output_schema` | PASS |
| `test_ts_id_is_unique_under_high_frequency_calls` | PASS |

## Modern 失败详情

### FAIL: `test_config_entrypoints.ConfigEntrypointsTests.test_project_facts_limit_should_affect_load_memory`

```text
Traceback (most recent call last):
  File "/Users/TerrellShe/Documents/personal/clawd.bot/tests/standalone-memory-skill/test_config_entrypoints.py", line 129, in test_project_facts_limit_should_affect_load_memory
    self.assertEqual(fact_count, 1, msg=f"期望受项目级配置限制为1条，实际为{fact_count}条\n{ctx}")
AssertionError: 2 != 1 : 期望受项目级配置限制为1条，实际为2条
## 核心记忆

# 核心记忆

## 用户偏好
- 语言：中文

## 项目背景
- 项目：standalone-test

## 重要决策

## 近期事实

- [W][2026-02-19] CFG_LIMIT_A
- [W][2026-02-19] CFG_LIMIT_B
```

### FAIL: `test_config_entrypoints.ConfigEntrypointsTests.test_reset_all_should_work`

```text
Traceback (most recent call last):
  File "/Users/TerrellShe/Documents/personal/clawd.bot/tests/standalone-memory-skill/test_config_entrypoints.py", line 91, in test_reset_all_should_work
    self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
AssertionError: 2 != 0 : usage: manage_memory.py config reset [-h] [--global] key
manage_memory.py config reset: error: the following arguments are required: key
```

## Legacy 输出摘录

```text
    ✓ sessionStart 成功
    ✓ sessionStart 包含刚写入的事实  (上下文长度=196, 包含token=True)
    ✓ partial 返回结果非空  (got 3)
    ✓ partial 包含最新记录（fact-5或6）  (contents=['fact-6', 'fact-5', 'fact-4'])
    ✓ partial 不是仅含最旧记录  (contents=['fact-6', 'fact-5', 'fact-4'])
    ✓ 100 次 ts_id 调用产生 100 个唯一值  (unique=100/100)

=================================================================
  测试用例汇总
=================================================================
  #    测试用例                                     通过     失败     跳过    
  --------------------------------------------------------------
  ✓ 1   lib/config.py 配置模块                     7      0      0     
  ✓ 2   lib/jsonl.py JSONL 读写                  8      0      0     
  ✓ 3   lib/sqlite_store.py SQLite 操作          11     0      0     
  ✓ 4   Chunk 分割与重叠策略                          9      0      0     
  ✓ 5   load_memory.py (sessionStart Hook)     10     0      0     
  ✓ 6   flush_memory.py (preCompact Hook)      10     0      0     
  ✓ 7   prompt_session_save.py (stop Hook)     10     0      0     
  ✓ 8   sync_and_cleanup.py (sessionEnd Hook)  10     0      0     
  ✓ 9   sync_index.py (JSONL → SQLite 同步)      11     0      0     
  ✓ 10  search_memory.py (Agent 搜索工具)          13     0      0     
  ✓ 11  init.py (一键初始化)                        10     0      0     
  ✓ 12  上下文完整性与端到端验证                           10     0      0     
  ✓ 13  端到端完整场景验证                              29     0      0     
  ✓ 14  缺陷修复回归验证                               7      0      0     
  --------------------------------------------------------------
  合计                                           155    0      0     

=================================================================
  结果: ALL PASSED
  总计: 155 项  通过: 155  失败: 0  跳过: 0
  通过率: 100.0%
  耗时: 199.18s
=================================================================

  MD 报告已输出: /Users/TerrellShe/Documents/personal/clawd.bot/tests/standalone-memory-skill/legacy/tests/2026-02-19-测试报告.md

[2026-02-19 17:24:29] [INFO] [memory.embedding] 从本地缓存加载模型 /Users/TerrellShe/.memory-skill/models/models--BAAI--bge-small-zh-v1.5
[2026-02-19 17:24:36] [INFO] [memory.embedding] 模型加载完成 dim=512 (耗时 6.6s)
```
