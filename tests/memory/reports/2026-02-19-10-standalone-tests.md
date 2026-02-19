# Standalone Memory Skill 测试报告

> 时间: 2026-02-19 18:27:35
> 结果: FAILED
> 耗时: 65.459s

## 汇总

| 指标 | 数值 |
|---|---:|
| 总用例 | 29 |
| 通过 | 26 |
| 失败 | 2 |
| 错误 | 0 |
| 跳过 | 1 |

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
| `test_reset_all_should_work` | SKIP |

### test_context_flow

| 用例 | 状态 |
|---|---|
| `test_lifecycle_session_start_precompact_stop_and_next_session` | PASS |

### test_e2e

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
| `test_ts_id_high_frequency_uniqueness` | FAIL |

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
  File "/Users/TerrellShe/Documents/personal/clawd.bot/tests/standalone-memory-skill/test_config.py", line 131, in test_project_facts_limit_should_affect_load_memory
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

### FAIL: `test_regression.DetailRegressionTests.test_ts_id_high_frequency_uniqueness`

```text
Traceback (most recent call last):
  File "/Users/TerrellShe/Documents/personal/clawd.bot/tests/standalone-memory-skill/test_regression.py", line 51, in test_ts_id_high_frequency_uniqueness
    self.assertEqual(len(values), len(set(values)))
AssertionError: 200 != 199
```
