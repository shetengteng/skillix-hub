# Wiki 索引

> 由 knowledge-compiler 自动维护。上次编译: {{YYYY-MM-DD}}
> 编译: `kc compile` | 健康检查: `kc lint` | 查询: `kc query <问题>`

<!-- AI 导航指南:
本文件是知识库的入口（Layer 1）。AI 收到知识相关问题时，先读本文件。
优先使用下方 Topic Registry 做首轮召回，不要逐篇打开 concepts/*.md。
导航路径: INDEX.md Registry → frontmatter（需要时）→ 正文 → 源文件
-->

## Topic Registry

<!-- 机器优先的注册表。每个 topic 仅且必须有一条记录。 -->
<!-- kc query / kc browse / kc status 优先依赖此表做召回，而非全文扫描。 -->

| slug | title | summary | tags | answers | coverage | updated | sources_count |
|------|-------|---------|------|---------|----------|---------|---------------|
| {{topic-slug}} | {{标题}} | {{2-3句摘要}} | {{tag1, tag2}} | {{问题1?; 问题2?}} | high/medium/low | YYYY-MM-DD | N |

## 分类视图

<!-- 给人浏览的分类视图。与 Registry 数据一致，但按分类组织。 -->

### {{分类名称}}

| 主题 | 摘要 | 覆盖度 | 更新日期 |
|------|------|--------|---------|
| [[concepts/{{topic-slug}}]] | 一句话描述 | high/medium/low | YYYY-MM-DD |

### 未分类

| 主题 | 摘要 | 覆盖度 | 更新日期 |
|------|------|--------|---------|

## 分析记录

| 页面 | 问题 | 日期 |
|------|------|------|
| [[analyses/{{slug}}]] | 问题摘要 | YYYY-MM-DD |

## 统计

- 总主题数: {{N}}
- 高覆盖: {{N}} | 中覆盖: {{N}} | 低覆盖: {{N}}
- 已索引源文件: {{N}} 个
