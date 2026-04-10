# Command: kc browse

Browse the knowledge map — an organized view of all compiled topics.

## Usage

```
kc browse                    # full knowledge map overview
kc browse <category>         # topics in a specific category
kc browse <topic-slug>       # read a single topic article
```

---

## Steps

### Mode 1: Full Overview (no arguments)

1. Read `wiki/INDEX.md`.
2. Read `wiki/schema.md` to get the category structure.
3. Present a structured overview:
   ```
   Knowledge Map
   ─────────────
   ## Architecture (5 topics)
     api-gateway-design      [high]  API 网关设计决策与实现方案
     event-driven-arch       [medium] 事件驱动架构模式
     ...

   ## Data Layer (3 topics)
     database-sharding       [high]  数据库分片策略
     ...

   ## Uncategorized (2 topics)
     misc-topic              [low]   ...
   ```
4. Coverage indicator is the dominant coverage level across the topic's sections.

### Mode 2: Category View (`kc browse <category>`)

1. Read `wiki/schema.md` to find topics in the requested category.
2. For each topic, read the frontmatter and Summary section from `wiki/concepts/{slug}.md`.
3. Present:
   ```
   Category: Architecture
   ──────────────────────
   api-gateway-design [high]
     API 网关设计决策与实现方案
     Sources: 3 files | Sections: 6 | Last updated: 2026-04-08
     Related: [[microservice-patterns]], [[load-balancing]]

   event-driven-arch [medium]
     事件驱动架构模式
     Sources: 2 files | Sections: 5 | Last updated: 2026-03-20
   ```

### Mode 3: Single Topic (`kc browse <topic-slug>`)

1. Read `wiki/concepts/{topic-slug}.md` in full.
2. Present the article content to the user.
3. Highlight sections with `low` coverage: "This section has low coverage — consider adding more sources or running `kc compile --topic <slug>`."
