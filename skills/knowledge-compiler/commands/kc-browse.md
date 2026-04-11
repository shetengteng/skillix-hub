# 命令: kc browse

浏览知识地图——所有已编译主题的结构化视图。

## 用法

```
kc browse                    # 完整知识地图概览
kc browse <category>         # 查看某个分类下的主题
kc browse <topic-slug>       # 阅读单个主题文章
```

---

## 步骤

### 模式 1: 完整概览（无参数）

1. 读取 `wiki/INDEX.md`。
2. 读取 `wiki/schema.md` 获取分类结构。
3. 展示结构化概览：
   ```
   知识地图
   ─────────────
   ## 架构 (5 个主题)
     api-gateway-design      [high]   API 网关设计决策与实现方案
     event-driven-arch       [medium] 事件驱动架构模式
     ...

   ## 数据层 (3 个主题)
     database-sharding       [high]   数据库分片策略
     ...

   ## 未分类 (2 个主题)
     misc-topic              [low]    ...
   ```
4. 覆盖度指标取该主题所有章节中的主要覆盖度级别。

### 模式 2: 分类视图 (`kc browse <category>`)

1. 读取 `wiki/schema.md` 查找请求分类中的主题。
2. 对每个主题，读取 `wiki/concepts/{slug}.md` 的 frontmatter 和概要章节。
3. 展示：
   ```
   分类: 架构
   ──────────────────────
   api-gateway-design [high]
     API 网关设计决策与实现方案
     来源: 3 个文件 | 章节: 6 | 最近更新: 2026-04-08
     相关: [[microservice-patterns]], [[load-balancing]]

   event-driven-arch [medium]
     事件驱动架构模式
     来源: 2 个文件 | 章节: 5 | 最近更新: 2026-03-20
   ```

### 模式 3: 单主题 (`kc browse <topic-slug>`)

1. 完整读取 `wiki/concepts/{topic-slug}.md`。
2. 向用户展示文章内容。
3. 标记覆盖度为 `low` 的章节："该章节覆盖度较低——考虑添加更多源材料或运行 `kc compile --topic <slug>`。"
