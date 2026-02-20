# Standalone Memory Skill 测试报告

> 时间: 2026-02-20 18:52:18
> 结果: PASSED
> 耗时: 230.918s

## 汇总

| 指标 | 数值 |
|---|---:|
| 总用例 | 140 |
| 通过 | 136 |
| 失败 | 0 |
| 错误 | 0 |
| 跳过 | 4 |

## 单元测试

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
| `test_project_facts_limit_should_affect_load_memory` | SKIP |
| `test_reset_all_should_work` | SKIP |

### test_db

| 用例 | 状态 |
|---|---|
| `test_db_no_database_file` | PASS |
| `test_db_query_rejects_write` | PASS |
| `test_db_query_select` | PASS |
| `test_db_schema_chunks` | PASS |
| `test_db_schema_nonexistent_table` | PASS |
| `test_db_show_chunks_with_limit` | PASS |
| `test_db_show_meta` | PASS |
| `test_db_stats_shows_counts` | PASS |
| `test_db_tables_after_init` | PASS |

### test_embedding

| 用例 | 状态 |
|---|---|
| `test_embed_batch_returns_list_of_vectors` | PASS |
| `test_embed_text_returns_float_list` | PASS |
| `test_embed_text_unavailable_returns_none` | SKIP |
| `test_get_dimensions_positive` | PASS |
| `test_get_dimensions_unavailable_returns_zero` | SKIP |
| `test_is_available_returns_bool` | PASS |

### test_file_lock

| 用例 | 状态 |
|---|---|
| `test_acquire_and_release` | PASS |
| `test_context_manager` | PASS |
| `test_creates_parent_directory` | PASS |
| `test_lock_path_property` | PASS |
| `test_reentrant_same_process` | PASS |
| `test_release_without_acquire_is_safe` | PASS |

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

### test_jsonl_manage

| 用例 | 状态 |
|---|---|
| `test_count_by_type` | PASS |
| `test_count_by_type_with_deleted` | PASS |
| `test_filter_by_date_range` | PASS |
| `test_filter_by_id` | PASS |
| `test_filter_by_keyword` | PASS |
| `test_filter_by_type` | PASS |
| `test_include_deleted_flag` | PASS |
| `test_purge_removes_permanently` | PASS |
| `test_purge_session_entry` | PASS |
| `test_read_all_entries_all_scope` | PASS |
| `test_read_all_entries_daily_scope` | PASS |
| `test_read_all_entries_sessions_scope` | PASS |
| `test_soft_delete_marks_entries` | PASS |
| `test_soft_delete_then_restore` | PASS |
| `test_write_audit_entry` | PASS |

### test_logger

| 用例 | 状态 |
|---|---|
| `test_get_logger_creates_log_directory` | PASS |
| `test_get_logger_idempotent` | PASS |
| `test_get_logger_returns_logger` | PASS |
| `test_logger_writes_to_file` | PASS |

### test_manage_helpers

| 用例 | 状态 |
|---|---|
| `test_all_dotpaths_empty` | PASS |
| `test_all_dotpaths_flat` | PASS |
| `test_all_dotpaths_nested` | PASS |
| `test_parse_value_bool_false` | PASS |
| `test_parse_value_bool_true` | PASS |
| `test_parse_value_float` | PASS |
| `test_parse_value_int` | PASS |
| `test_parse_value_string` | PASS |

### test_regression

| 用例 | 状态 |
|---|---|
| `test_decay_prefers_newest_partial_window` | PASS |
| `test_fact_recall_pipeline` | PASS |
| `test_ts_id_high_frequency_uniqueness` | PASS |

### test_save_summary

| 用例 | 状态 |
|---|---|
| `test_save_summary_appends_to_existing` | PASS |
| `test_save_summary_creates_sessions_jsonl` | PASS |
| `test_save_summary_empty_decisions_and_todos` | PASS |
| `test_save_summary_requires_topic_and_summary` | PASS |

### test_sqlite

| 用例 | 状态 |
|---|---|
| `test_cosine_similarity_edges` | PASS |
| `test_upsert_fts_meta_sync_state` | PASS |

### test_unit_core

| 用例 | 状态 |
|---|---|
| `test_partial_window_prefers_latest_entries` | PASS |
| `test_save_fact_cli_output_schema` | PASS |

### test_update

| 用例 | 状态 |
|---|---|
| `test_update_does_not_duplicate_hooks` | PASS |
| `test_update_installs_rules_with_placeholders_resolved` | PASS |
| `test_update_merges_hooks` | PASS |
| `test_update_output_messages` | PASS |
| `test_update_preserves_data_directory` | PASS |
| `test_update_replaces_code` | PASS |
| `test_update_resolves_placeholders_in_skill_md` | PASS |
| `test_missing_source_dir` | PASS |
| `test_requires_source_argument` | PASS |
| `test_skill_not_installed` | PASS |

### test_utils

| 用例 | 状态 |
|---|---|
| `test_date_range_returns_correct_count` | PASS |
| `test_date_range_zero_returns_empty` | PASS |
| `test_iso_now_format` | PASS |
| `test_parse_iso_invalid_returns_min` | PASS |
| `test_parse_iso_valid` | PASS |
| `test_parse_iso_without_z` | PASS |
| `test_today_str_format` | PASS |
| `test_ts_id_format_and_uniqueness` | PASS |
| `test_utcnow_returns_utc_datetime` | PASS |

## 集成测试

### test_context_flow

| 用例 | 状态 |
|---|---|
| `test_lifecycle_session_start_precompact_stop_and_next_session` | PASS |

### test_hook_contracts

| 用例 | 状态 |
|---|---|
| `test_flush_memory_returns_user_message_contract` | PASS |
| `test_load_memory_returns_additional_context_json` | PASS |
| `test_prompt_session_save_completed_returns_followup` | PASS |
| `test_prompt_session_save_non_completed_returns_empty_json` | PASS |

### test_load_memory_auto_init

| 用例 | 状态 |
|---|---|
| `test_auto_created_memory_md_loaded_in_context` | PASS |
| `test_auto_creates_daily_dir` | PASS |
| `test_auto_creates_memory_md_when_missing` | PASS |
| `test_does_not_overwrite_existing_memory_md` | PASS |
| `test_session_start_logged_in_new_project` | PASS |

### test_memory_disable

| 用例 | 状态 |
|---|---|
| `test_flush_memory_returns_empty_when_disabled` | PASS |
| `test_hooks_work_normally_after_removing_disable_file` | PASS |
| `test_is_memory_enabled_returns_false_when_disable_file_exists` | PASS |
| `test_is_memory_enabled_returns_true_after_removing_disable_file` | PASS |
| `test_is_memory_enabled_returns_true_by_default` | PASS |
| `test_load_memory_does_not_create_daily_when_disabled` | PASS |
| `test_load_memory_returns_empty_context_when_disabled` | PASS |
| `test_prompt_session_save_returns_empty_when_disabled` | PASS |
| `test_sync_and_cleanup_returns_empty_when_disabled` | PASS |

### test_sync_search

| 用例 | 状态 |
|---|---|
| `test_search_memory_fts_hybrid_and_missing_index` | PASS |
| `test_sync_index_build_incremental_rebuild` | PASS |

### test_time_range_search

| 用例 | 状态 |
|---|---|
| `test_combined_filters` | PASS |
| `test_days_filter` | PASS |
| `test_from_date_filter` | PASS |
| `test_no_filters` | PASS |
| `test_to_date_filter` | PASS |
| `test_export_with_days` | PASS |
| `test_export_with_old_date_range_empty` | PASS |
| `test_search_with_date_range_no_results` | PASS |
| `test_search_with_days_arg` | PASS |
| `test_fts_with_date_range` | PASS |
| `test_fts_with_days_filter` | PASS |
| `test_hybrid_with_days_filter` | PASS |

## 端到端测试

### test_e2e

| 用例 | 状态 |
|---|---|
| `test_saved_daily_fact_loaded_by_session_start` | PASS |
| `test_session_end_sync_makes_new_fact_searchable` | PASS |

### test_init

| 用例 | 状态 |
|---|---|
| `test_init_creates_hooks_rules_data_and_is_idempotent` | PASS |

### test_manage_e2e

| 用例 | 状态 |
|---|---|
| `test_delete_no_match_returns_zero` | PASS |
| `test_delete_preview_without_confirm` | PASS |
| `test_delete_purge_removes_permanently` | PASS |
| `test_delete_soft_with_confirm` | PASS |
| `test_delete_then_restore_by_id` | PASS |
| `test_edit_content` | PASS |
| `test_edit_without_id_fails` | PASS |
| `test_export_returns_records` | PASS |
| `test_export_to_file` | PASS |
| `test_doctor_returns_checks` | PASS |
| `test_list_pagination` | PASS |
| `test_list_returns_json_with_records` | PASS |
| `test_list_with_keyword_filter` | PASS |
| `test_stats_returns_disk_and_daily_info` | PASS |
