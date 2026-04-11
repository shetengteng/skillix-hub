# 命令: kc browse

浏览知识地图。采用 **Registry → 元数据 → 正文** 三层渐进展开。

## 用法

```
kc browse                    # Layer 1: Registry 概览
kc browse <category>         # Layer 2: 分类下的 topic 元数据
kc browse <topic-slug>       # Layer 3: 展开单个 topic 正文
```

---

## Layer 1: Registry 概览（无参数）

1. 读取 `wiki/INDEX.md` 的 **Topic Registry** 表。
2. 按分类分组展示：

   ```
   知识地图
   ─────────────
   ## 架构 (3 个主题)
     api-gateway-design      [high]   API 网关的职责边界与认证策略
     event-driven-arch       [medium] 事件驱动架构模式
     microservice-patterns   [medium] 微服务通信模式

   ## 数据层 (2 个主题)
     database-sharding       [high]   数据库分片策略
     cache-strategy          [low]    缓存层设计

   总计: 5 个主题 | 高: 2 | 中: 2 | 低: 1
   ```

3. 数据直接来自 Registry，**不读取 concepts/ 文件**。

---

## Layer 2: 分类/Topic 元数据 (`kc browse <category>` 或 `<slug>`)

1. 从 Registry 中筛选指定分类或 topic。
2. 读取对应 `wiki/concepts/{slug}.md` 的 **frontmatter**（不读正文）。
3. 展示元数据：

   ```
   主题: api-gateway-design [high]
   ─────────────────────────
   摘要: API 网关的职责边界、认证策略与入口流量治理方案。
   标签: api-gateway, auth, traffic, jwt
   能回答:
     - API 网关做了哪些设计取舍？
     - 认证在什么层处理？
     - 网关负责哪些入口流量能力？
   来源: 3 个文件 | 章节: 6 | 上次更新: 2026-04-08
   相关: [[auth-flow]], [[load-balancing]]
   ```

---

## Layer 3: 展开正文 (`kc browse <topic-slug> --full`)

1. 完整读取 `wiki/concepts/{topic-slug}.md`。
2. 向用户展示文章内容。
3. 标记覆盖度为 `low` 的章节：
   "该章节覆盖度较低——考虑添加更多源材料或运行 `kc compile --topic <slug>`。"

---

## 注意事项

- **逐层展开**。Layer 1 不读文件，Layer 2 只读 frontmatter，Layer 3 才读全文。
- 如果用户直接说 `kc browse <slug>`（不带 --full），默认展示 Layer 2（元数据）。
- 用户说"详细看看"或"展开"时，进入 Layer 3。
