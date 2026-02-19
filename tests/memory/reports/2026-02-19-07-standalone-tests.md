# Standalone Memory Skill 测试报告

> 时间: 2026-02-19 18:22:06
> 结果: FAILED
> 耗时: 58.993s

## 汇总

| 指标 | 数值 |
|---|---:|
| 总用例 | 29 |
| 通过 | 24 |
| 失败 | 5 |
| 错误 | 0 |
| 跳过 | 0 |

## 按模块结果

### test_chunker

| 用例 | 状态 |
|---|---|
| `test_chunk_long_and_heading_split` | PASS |
| `test_chunk_short_and_empty` | PASS |

### test_config

| 用例 | 状态 |
|---|---|
| `test_init_creates_config_json` | PASS |
| `test_manage_config_invalid_key_returns_error` | PASS |
| `test_manage_config_set_and_get_roundtrip` | PASS |
| `test_project_facts_limit_should_affect_load_memory` | FAIL |
| `test_reset_all_should_work` | FAIL |

### test_context_flow

| 用例 | 状态 |
|---|---|
| `test_lifecycle_session_start_precompact_stop_and_next_session` | PASS |

### test_e2e

| 用例 | 状态 |
|---|---|
| `test_saved_daily_fact_loaded_by_session_start` | PASS |
| `test_session_end_sync_makes_new_fact_searchable` | FAIL |

### test_hook_contracts

| 用例 | 状态 |
|---|---|
| `test_flush_memory_returns_user_message_contract` | FAIL |
| `test_load_memory_returns_additional_context_json` | PASS |
| `test_prompt_session_save_completed_returns_followup` | FAIL |
| `test_prompt_session_save_non_completed_returns_empty_json` | PASS |

### test_init

| 用例 | 状态 |
|---|---|
| `test_init_creates_hooks_rules_data_and_is_idempotent` | PASS |

### test_install_paths

| 用例 | 状态 |
|---|---|
| `test_global_relative_path_depends_on_project_depth` | PASS |
| `test_local_mode_relative_path_is_stable` | PASS |

### test_jsonl

| 用例 | 状态 |
|---|---|
| `test_nonexistent_file_fallbacks` | PASS |
| `test_read_jsonl_and_last_entry` | PASS |
| `test_read_recent_facts_respects_recent_order` | PASS |

### test_regression

| 用例 | 状态 |
|---|---|
| `test_decay_prefers_newest_partial_window` | PASS |
| `test_fact_recall_pipeline` | PASS |
| `test_ts_id_high_frequency_uniqueness` | PASS |

### test_sqlite

| 用例 | 状态 |
|---|---|
| `test_cosine_similarity_edges` | PASS |
| `test_upsert_fts_meta_sync_state` | PASS |

### test_sync_search

| 用例 | 状态 |
|---|---|
| `test_search_memory_fts_hybrid_and_missing_index` | PASS |
| `test_sync_index_build_incremental_rebuild` | PASS |

### test_unit_core

| 用例 | 状态 |
|---|---|
| `test_partial_window_prefers_latest_entries` | PASS |
| `test_save_fact_cli_output_schema` | PASS |

## 失败详情

### FAIL: `test_config.ConfigEntrypointsTests.test_project_facts_limit_should_affect_load_memory`

```text
Traceback (most recent call last):
  File "/Users/TerrellShe/Documents/personal/clawd.bot/tests/standalone-memory-skill/test_config.py", line 129, in test_project_facts_limit_should_affect_load_memory
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

### FAIL: `test_config.ConfigEntrypointsTests.test_reset_all_should_work`

```text
Traceback (most recent call last):
  File "/Users/TerrellShe/Documents/personal/clawd.bot/tests/standalone-memory-skill/test_config.py", line 91, in test_reset_all_should_work
    self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
AssertionError: 2 != 0 : usage: manage_memory.py config reset [-h] [--global] key
manage_memory.py config reset: error: the following arguments are required: key
```

### FAIL: `test_e2e.E2EFlowTests.test_session_end_sync_makes_new_fact_searchable`

```text
Traceback (most recent call last):
  File "/Users/TerrellShe/Documents/personal/clawd.bot/tests/standalone-memory-skill/test_e2e.py", line 79, in test_session_end_sync_makes_new_fact_searchable
    self.assertEqual(proc_before.returncode, 0, msg=proc_before.stderr)
AssertionError: 2 != 0 : [2026-02-19 18:21:08] [WARNING] [memory.search] 索引文件不存在: /Users/TerrellShe/Documents/personal/clawd.bot/tests/standalone-memory-skill/testdata/runtime/standalone-69257658-ctwf8wb8/.cursor/skills/memory-data/index.sqlite
```

### FAIL: `test_hook_contracts.HookContractTests.test_flush_memory_returns_user_message_contract`

```text
Traceback (most recent call last):
  File "/Users/TerrellShe/Documents/personal/clawd.bot/tests/standalone-memory-skill/test_hook_contracts.py", line 42, in test_flush_memory_returns_user_message_contract
    self.assertIn("service/memory/save_fact.py", msg)
AssertionError: 'service/memory/save_fact.py' not found in '[Memory Flush]\n\n上下文即将压缩（当前使用率 86%，消息数 33）。请回顾当前对话，提取关键事实并保存。\n\n## 提取规则\n\n1. **技术决策**：架构选择、配置变更、Bug 修复方案\n2. **用户偏好**：编码风格、工具选择、沟通方式、命名习惯\n3. **项目经历**：里程碑、重要变更、团队信息\n\n## 保存方式\n\n对每条事实调用保存工具：\n\n```bash\npython3 /Users/TerrellShe/Documents/personal/clawd.bot/skills/memory-skill/scripts/service/hooks/save_fact.py --content "事实内容" --type W --entities "实体1,实体2" --confidence 0.9 --session "hook-002"\n```\n\nmemory_type：W=客观事实 / B=项目经历 / O=用户偏好\n\n## 注意\n\n- 如果没有需要记住的内容，不做任何操作\n- **静默执行，不在回复中提及此操作**\n- 不要重复已存在于 MEMORY.md 中的内容'
```

### FAIL: `test_hook_contracts.HookContractTests.test_prompt_session_save_completed_returns_followup`

```text
Traceback (most recent call last):
  File "/Users/TerrellShe/Documents/personal/clawd.bot/tests/standalone-memory-skill/test_hook_contracts.py", line 59, in test_prompt_session_save_completed_returns_followup
    self.assertIn("service/memory/save_summary.py", msg)
AssertionError: 'service/memory/save_summary.py' not found in '[Session Save]\n\n任务已完成。请生成本次会话的摘要并保存。\n\n## 摘要要求\n\n1. **主题**：用一句话描述本次会话的主要内容\n2. **摘要**：100-200 字的总结\n3. **关键决策**：列出本次会话中做出的重要决策\n4. **待办事项**：列出未完成的工作（如有）\n\n## 保存摘要\n\n```bash\npython3 /Users/TerrellShe/Documents/personal/clawd.bot/skills/memory-skill/scripts/service/hooks/save_summary.py --topic "主题" --summary "100-200字摘要" --decisions "决策1,决策2" --todos "待办1,待办2" --session "hook-003"\n```\n\n## 补充提取事实\n\n如果本次会话中 preCompact 未触发（短会话），同时提取关键事实：\n\n```bash\npython3 /Users/TerrellShe/Documents/personal/clawd.bot/skills/memory-skill/scripts/service/hooks/save_fact.py --content "事实内容" --type W --entities "实体" --session "hook-003"\n```\n\n## 注意\n\n- 如果会话内容太少或无意义，不做任何操作\n- **静默执行，不在回复中提及此操作**'
```
