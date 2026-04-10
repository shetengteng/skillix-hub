# Command: kc status

Show a summary of the knowledge base health and statistics.

## Usage

```
kc status
```

---

## Steps

1. **Verify config.** Check that `.kc-config.json` exists. If not: "No knowledge base found. Run `kc init` first."

2. **Count source files:**
   ```bash
   find raw/ -name "*.md" | wc -l
   ```
   Break down by subdirectory (designs, decisions, research, notes).

3. **Count compiled topics:**
   ```bash
   ls wiki/concepts/*.md 2>/dev/null | wc -l
   ```

4. **Read coverage distribution.** Scan all `wiki/concepts/*.md` files and count coverage tags:
   - Total sections across all topics
   - Count of high / medium / low tags

5. **Check staleness.** Read `.compile-state.json` and compare mtimes:
   - How many source files changed since last compile?
   - How many topics are >30 days since last update?

6. **Read last compile info** from `wiki/log.md` (last entry).

7. **Report:**
   ```
   Knowledge Base Status
   ─────────────────────
   Sources:     42 files (12 designs, 8 decisions, 15 research, 7 notes)
   Topics:      18 compiled concepts
   Coverage:    high 45% | medium 35% | low 20%
   Freshness:   3 sources changed since last compile
                2 topics >30 days old
   Last compile: 2026-04-08 (incremental, 3 topics updated)
   Config:      session_mode=recommended

   Suggested actions:
     - Run `kc compile` to process 3 changed sources
     - Run `kc lint` to check 2 aging topics
   ```
