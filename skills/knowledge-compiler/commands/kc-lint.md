# Command: kc lint

Run a health check on the wiki. Detects structural problems and optionally fixes them.

## Usage

```
kc lint                  # report only
kc lint --fix            # report and auto-fix where safe
```

---

## Steps

1. **Verify config.** Check that `.kc-config.json` exists and `wiki/` directory has content.

2. **Load quality gates.** Read [references/quality-gates.md](../references/quality-gates.md) for the full gate definitions.

3. **Run Hard Gate checks:**

   | Check | What to do |
   |-------|-----------|
   | Frontmatter complete | Scan each `wiki/concepts/*.md` for required YAML fields: `id`, `title`, `sources`, `created`, `updated` |
   | Coverage tags | Verify every `## Section` has a `<!-- coverage: X -->` comment |
   | Source references valid | Check every `[source: path]` points to an existing file |
   | Schema consistency | Every topic in `wiki/concepts/` has an entry in `wiki/schema.md` |
   | Non-empty content | Every section has content beyond the heading |

4. **Run Soft Gate checks:**

   | Check | What to do |
   |-------|-----------|
   | Stale articles | Compare source file mtimes against `.compile-state.json` — flag sources that changed since last compile |
   | Orphan pages | Find wiki pages with no inbound `[[links]]` from INDEX.md or other articles |
   | Missing cross-references | Find topics mentioned in text but not linked with `[[slug]]` |
   | Low coverage clusters | Flag topics where all sections are `low` coverage |
   | Content contradictions | Identify conflicting claims across topic articles |
   | Schema drift | Find topics in wiki/ not reflected in schema.md |
   | Broken wiki links | Find `[[slug]]` references pointing to non-existent concept pages |
   | Missing frontmatter fields | Pages lacking optional but recommended fields (tags, relations) |

5. **Report:**
   ```
   kc lint report — YYYY-MM-DD
   ──────────────────────────────────
   Hard Gates: X passed, Y failed
     [FAIL] wiki/concepts/rag.md — missing coverage tag on ## Gotchas
     [FAIL] wiki/concepts/moe.md — [source: raw/old-file.md] file not found

   Soft Gates: N warnings
     [STALE]   wiki/concepts/api-design.md — sources changed 5 days ago
     [ORPHAN]  wiki/concepts/old-topic.md — no inbound links
     [LOW-COV] wiki/concepts/moe.md — 4/5 sections are low coverage

   2 auto-fixable issues. Fix? (y/n)
   ```

6. **Auto-fix** (if `--fix` flag):
   - Add missing `<!-- coverage: low -->` tags.
   - Add missing topics to schema.md.
   - Remove references to deleted source files (with warning).
   - Ask confirmation before each fix if it modifies content.

7. **Log.** Append to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] lint | X hard gate issues, Y soft gate warnings, Z fixed
   ```
