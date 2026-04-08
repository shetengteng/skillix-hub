# Knowledge Base Skill 测试设计

## 测试范围

| 模块 | 文件 | 说明 |
|------|------|------|
| indexer | src/indexer.py | JSONL 读写、ID 生成、类型检测、哈希、标题提取、分类推断、CRUD |
| scanner | src/scanner.py | 内容提取、变更检测、编译清单、缓存 |
| compiler | src/compiler.py | frontmatter 解析、概念加载、编译后处理、标记更新 |
| browser | src/browser.py | 渐进式浏览（L1-L4）、内容输出 |
| searcher | src/searcher.py | 关键词搜索、评分、状态统计、路径检查 |
| graph | src/graph.py | 图谱加载、子图提取、Mermaid 输出、概念/分类管理 |

## 测试用例

### 模块：indexer

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| read_index 空文件 | 空 index.jsonl | 返回 [] | unit |
| write + read 往返 | 2 条目 | 读回 2 条 | unit |
| 损坏行跳过 | JSONL 含非法行 | 跳过损坏行 | unit |
| 覆盖写入 | 写两次 | 第二次覆盖 | unit |
| generate_id 格式 | 无 | kb-YYYYMMDD-HHMMSS-NNN | unit |
| generate_id 唯一性 | 10 次调用 | 10 个不同 ID | unit |
| detect_type markdown | .md 文件 | "markdown" | unit |
| detect_type image | .png 文件 | "image" | unit |
| detect_type dataset | .csv 文件 | "dataset" | unit |
| detect_type repo | 含 .git 目录 | "repo" | unit |
| detect_type directory | 普通目录 | "directory" | unit |
| detect_type 未知 | .txt 文件 | "markdown" (默认) | unit |
| compute_hash markdown | md 文件 | 8 位十六进制 | unit |
| compute_hash 相同内容 | 两个相同文件 | 哈希相同 | unit |
| compute_hash 不同内容 | 两个不同文件 | 哈希不同 | unit |
| compute_hash 不存在 | 无效路径 | 返回 "" | unit |
| compute_hash image | png 文件 | 基于 stat 的哈希 | unit |
| extract_title H1 | 含 # 标题的 md | 返回标题文字 | unit |
| extract_title 无标题 | 无 H1 的 md | 返回文件名 stem | unit |
| extract_title 不存在 | 无效路径 | 返回 stem | unit |
| extract_title 图片 | png 文件 | 返回文件名 stem | unit |
| infer_category design/ | design/memory/doc.md | "memory" | unit |
| infer_category 嵌套 | a/b/design/skill-store/x.md | "skill-store" | unit |
| infer_category 无 design | docs/readme.md | "uncategorized" | unit |
| infer_category 直接文件 | design/overview.md | "uncategorized" | unit |

### 模块：scanner

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| scan_entry markdown | 有效 md 条目 | status=ok, content_preview 含内容 | unit |
| scan_entry 路径不存在 | 无效路径条目 | status=invalid | unit |
| scan_entry link | link 类型条目 | status=ok, "外部链接" | unit |
| scan_entry image | png 条目 | status=ok, "图片" | unit |
| detect_changes 全新 | 5 个 compiled=false | new=5, changed=0 | unit |
| detect_changes 已编译 | 全部 compiled=true | new=0 | unit |
| detect_changes 失效 | 路径不存在的条目 | invalid=1 | unit |
| build_pending 增量 | 5 条新条目 | 返回 5 个 | unit |
| build_pending 全量 | 1 已编译 + 4 新 | 增量=4, 全量=5 | unit |
| build_pending 空索引 | 空 | 返回 [] | unit |
| cache 写入读取 | 字符串 | 读回相同内容 | unit |
| cache 缺失 | 不存在的 ID | 返回 None | unit |
| update_hashes | 旧哈希条目 | 更新为新哈希 | unit |

### 模块：compiler

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| parse_frontmatter 正常 | 含 frontmatter 的 md | 返回 dict | unit |
| parse_frontmatter 无 | 无 frontmatter | 返回 None | unit |
| parse_frontmatter 不存在 | 无效路径 | 返回 None | unit |
| load_existing_concepts 空 | 空 concepts/ | 返回 [] | unit |
| load_existing_concepts 有数据 | 3 个概念文件 | 返回 3 个 | unit |
| compile_finalize 正常 | 2 概念 + 2 源 | 生成 backlinks + graph + index.md | unit |
| compile_finalize 标记 | 概念引用 kb-src-1 | kb-src-1 标记 compiled | unit |
| compile_finalize 空 | 空 concepts/ | 输出警告 | unit |

### 模块：browser + searcher

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| browse 空 | 空索引 | "知识库为空" | unit |
| browse 有数据 | 5 条目 | 显示分类统计 | unit |
| browse wiki | wiki/index.md 存在 | 显示 wiki 内容 | unit |
| browse category 存在 | "test-skill" | 显示条目列表 | unit |
| browse category 不存在 | "nonexistent" | "未找到分类" | unit |
| source 存在 | 有效 ID | 显示详情 | unit |
| source 不存在 | 无效 ID | "未找到" | unit |
| match_score 标题 | "memory" | 分数 > 0 | unit |
| match_score 标签 | 标签匹配 | 分数 > 0 | unit |
| match_score 无匹配 | 不相关查询 | 分数 = 0 | unit |
| match_score 精确更高 | 完整 vs 部分 | 完整分数更高 | unit |
| text_match_score 精确 | 精确短语 | 分数 > 0 | unit |
| text_match_score 计数 | 重复出现 | 分数 >= 3 | unit |
| search 找到 | 匹配查询 | "搜索结果" | unit |
| search 无结果 | 不匹配查询 | "没有找到" | unit |
| status | 5 条目 | 显示统计 | unit |
| check 全有效 | 5 有效路径 | "有效: 5" | unit |
| check 有失效 | 1 无效路径 | "失效: 1" | unit |

### 模块：graph

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| load_graph 空 | 无 graph.json | nodes=[], edges=[] | unit |
| load_graph 有数据 | 4 节点 3 边 | 返回完整图 | unit |
| subgraph depth=1 | center=concept-a | 包含直接邻居 | unit |
| subgraph depth=2 | center=concept-a | 包含 2 跳内节点 | unit |
| subgraph 不存在 | nonexistent | nodes=[] | unit |
| mermaid_id | "concept-test" | "concept_test" | unit |
| category_rename | old→new | 所有条目更新 | unit |
| category_rename 不存在 | "nope" | "未找到分类" | unit |
| concept_remove | 有效 ID | 文件删除 | unit |
| concept_rename | 有效 ID + 新标题 | 文件内容更新 | unit |

## 测试策略

- **隔离**：所有测试使用 pytest `tmp_path` fixture 创建临时数据目录
- **不依赖外部**：不依赖网络、不依赖实际项目数据
- **覆盖边界**：空索引、损坏数据、路径不存在、重复操作等边界情况
- **运行时间**：目标 < 1 秒完成全部测试
