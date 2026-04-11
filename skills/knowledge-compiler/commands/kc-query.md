# 命令: kc query

基于 wiki 回答问题。采用 **Registry → Frontmatter → 正文 → 源文件** 四阶段检索。

## 用法

```
kc query <问题>
kc query <问题> --save       # 将回答保存到 wiki/analyses/
```

---

## 检索流程（4 阶段）

### 阶段 1 — Registry 召回

1. 读取 `wiki/INDEX.md` 的 **Topic Registry** 表。
2. 基于用户问题，匹配 Registry 中的 `summary`、`tags`、`answers` 字段。
3. 产出候选 topic 列表（通常 1-3 个）。
4. **如果 0 命中**：报告"当前 wiki 中没有相关主题"并建议添加源材料。

> 不要在此阶段打开任何 `concepts/*.md` 文件。Registry 应包含足够的信息做首轮筛选。

### 阶段 2 — Frontmatter 精筛

仅对阶段 1 召回的候选 topic：
1. 读取 `wiki/concepts/{slug}.md` 的 YAML frontmatter。
2. 对比 `answers` 字段与用户问题，确认相关性。
3. 排除 frontmatter 明显不匹配的 topic。
4. 确定最终要读取正文的 topic 列表（通常 1-2 个）。

### 阶段 3 — 正文检索

仅对阶段 2 确认的 topic：
1. 读取文章正文。
2. 按覆盖度分级处理：

   | 覆盖度 | AI 行为 |
   |--------|--------|
   | `high` | 直接引用，无需附加说明。 |
   | `medium` | 引用但加注："*（基于单一来源，可能需补充）*"。高风险决策问题额外进入阶段 4。 |
   | `low` | 必须进入阶段 4 回查源文件。 |

3. 合成回答，附带引用：
   - Wiki 引用：`[wiki: concepts/topic-slug.md]`
   - 源文件引用：`[source: path/to/file.md]`

### 阶段 4 — 源文件验证（按需）

仅在以下情况触发：
- 相关章节覆盖度为 `low`
- `session_mode=recommended/primary` 且涉及高风险决策
- 正文信息不足以完整回答

1. 从 frontmatter `sources` 字段获取源文件路径。
2. 读取源文件中与问题相关的部分。
3. 补充到回答中，标注来源。

---

## 保存分析

如果设置了 `--save`，或回答涉及多主题综合分析：
- 询问用户："这个回答值得保留。保存到 `wiki/analyses/`？(y/n)"
- 是 → 创建 `wiki/analyses/{YYYY-MM-DD}-{question-slug}.md`
- 在 `wiki/INDEX.md` 的分析记录区域添加条目

---

## 日志

追加到 `wiki/log.md`：
```
## [YYYY-MM-DD] query | <问题摘要>
- 召回主题: [slug1, slug2]
- 读取正文: [slug1]
- 回查源文件: 是/否
```

---

## 注意事项

- **Registry 是首轮入口**。不要跳过 Registry 直接读 concepts/。
- **最小化读取**。只读与问题相关的 topic，不要全量扫描。
- 保存的分析结果成为 wiki 的一部分，可被后续查询引用。
