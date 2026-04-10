# Skill: wiki-compiler

## Purpose

Compile a markdown knowledge base into a structured, AI-queryable wiki. Discovers topics automatically, tracks coverage confidence per section, and supports incremental recompilation on change.

## When to Activate

This skill activates when the user invokes `kc compile`, or when another command delegates to `wiki-compiler`.

---

## Input

Read `.kc-config.json` in the project root for configuration:

```json
{
  "session_mode": "recommended",
  "sources": ["raw/designs", "raw/decisions", "raw/research", "raw/notes"],
  "output_dir": "wiki",
  "exclude": ["raw/assets"],
  "compile_options": {
    "parallel_topics": true,
    "max_parallel": 4
  }
}
```

---

## Compilation Pipeline (5 Phases)

### Phase 1 — Scan Sources

1. Read `.compile-state.json` to get the previous compilation snapshot (file paths + mtimes).
2. Walk all directories listed in `sources`.
3. For each `.md` file found, get the current modification time:
   ```bash
   stat -f "%m" <file>     # macOS
   stat -c "%Y" <file>     # Linux
   ```
4. Compare current mtime to the snapshot.
5. Produce three lists: `new_files`, `changed_files`, `deleted_files`.
6. If `--full` flag is set, treat ALL source files as changed regardless of state.
7. If `.compile-state.json` does not exist, treat all files as new.

**Output:** `scan_result = { new, changed, deleted }`

**Quick exit:** If all three lists are empty, report "Nothing to compile — all topics up to date." and stop.

---

### Phase 2 — Classify & Discover Topics

For each file in `new_files + changed_files`:
1. Read: file path, H1 title (or filename if no H1), and first 500 characters of content.
2. Infer a topic slug: `lowercase-kebab-case` (e.g. `api-gateway-design`, `event-driven-architecture`).
3. Group files by topic. A single file may belong to multiple topics if it covers distinct subjects.
4. Cross-reference with existing `wiki/INDEX.md` to reuse established topic slugs where possible.
5. Flag genuinely new topics for Phase 3 article creation.

**Output:** `topic_map = { topic_slug: [file_paths] }`

**Rules:**
- Prefer merging into an existing topic over creating a new one.
- When uncertain, ask the user: "Found content that could be `topic-a` or `topic-b` — which topic fits better?"
- If `--topic <slug>` was specified, only process that single topic.

---

### Phase 3 — Compile Topic Articles

For each topic with changed source files:

1. **Read** ALL source files belonging to that topic in full.
2. **Check** if `wiki/concepts/{topic-slug}.md` already exists.
   - If it exists: read the current article, identify user-edited sections (sections without `[source: ...]` citations, or where the user modified compiler-generated content). Preserve these.
   - If new: create from `templates/article.md`.
3. **Generate** the article content:
   - Fill each section from the template with synthesized information from sources.
   - Assign a **coverage tag** to each section:
     - `high` — multiple sources, consistent, well-documented
     - `medium` — single source or partial coverage
     - `low` — inferred or sparse; reader should verify against raw/
   - Add `[source: raw/path/to/file.md]` citations inline wherever information is drawn from a source.
4. **Merge** with existing content:
   - Compiler-generated sections (with `[source: ...]`): update with new synthesis.
   - User-edited sections (no source citations or manually adjusted): keep the user's version.
   - New sections from sources not previously covered: append.

**Parallelism:** If `compile_options.parallel_topics` is true and there are 3+ topics to compile, process topics in parallel batches (up to `max_parallel`).

**Output:** Updated or created `wiki/concepts/{topic-slug}.md` files.

---

### Phase 3.5 — Schema

- **First run:** Generate `wiki/schema.md` from `templates/schema.md`. Infer topic taxonomy, naming conventions, and cross-reference rules from the compiled articles.
- **Subsequent runs:** Incrementally update schema only when new topics are added or existing topics are restructured. Never overwrite manual edits to schema.md.
- Schema is a shared contract between the human and the compiler. Treat it as authoritative for topic naming and categorization.

---

### Phase 4 — Update INDEX + Verify

#### 4a. Update INDEX.md

Rewrite `wiki/INDEX.md` using `templates/index.md`:
- List all topics with one-line description and coverage summary.
- Group by category (infer from schema.md if available).
- Mark new/updated topics with `[updated: YYYY-MM-DD]`.

#### 4b. Hard Gate Verification

Run these checks. If any fail, report the failure and attempt to fix before proceeding:

| Gate | Check | On Fail |
|------|-------|---------|
| Frontmatter complete | Every concept article has `id`, `title`, `sources`, `created`, `updated` in YAML frontmatter | Add missing fields |
| Coverage tags | Every `## Section` has a `<!-- coverage: X -->` comment | Add `<!-- coverage: low -->` as default |
| Source references valid | Every `[source: path]` points to a file that exists in raw/ | Remove invalid references, warn user |
| Schema consistency | Every compiled topic appears in `wiki/schema.md` | Add missing entries to schema |
| Non-empty content | Every section has substantive content beyond the heading | Flag empty sections with `[NEEDS INPUT: no source content available]` |

#### 4c. Soft Gate Checks

Run these checks and report warnings (do not block):

| Gate | Check |
|------|-------|
| Orphan pages | Wiki pages with no inbound links from INDEX.md or other articles |
| Low coverage clusters | Topics where all sections are tagged `low` |
| Stale detection | Source files changed since last compile (mtime), or concept >30 days since update |
| Content contradictions | Conflicting claims across topic articles on the same subject |
| Broken wiki links | `[[topic-slug]]` references pointing to non-existent pages |
| Missing cross-references | Topics mentioned in articles but not linked to their own page |

---

### Phase 5 — State & Log

1. **Update `.compile-state.json`:**
```json
{
  "last_compiled": "YYYY-MM-DD",
  "files": {
    "raw/designs/api-gateway.md": {
      "mtime": 1234567890,
      "topics": ["api-gateway-design"]
    }
  }
}
```

2. **Append to `wiki/log.md`:**
```markdown
## [YYYY-MM-DD] compile | incremental
- Topics compiled: X new, Y updated, Z unchanged
- Files processed: A new, B changed, C deleted
- New topics: [list]
- Updated topics: [list]
- Hard Gate: all passed / N issues fixed
- Soft Gate: N warnings
```

---

## Dry Run Mode

If `--dry-run` flag is set:
- Run Phase 1 and Phase 2 only.
- Output a preview: which files changed, which topics would be compiled, estimated scope.
- Do not write any files.

---

## Single Topic Mode

If `--topic <slug>` flag is set:
- Skip Phase 1 scan. Instead, look up the topic in `.compile-state.json` to find its source files.
- Run Phase 2 only for that topic's files.
- Run Phase 3 for that single topic.
- Run Phase 3.5, 4, 5 as normal.

---

## Error Handling

- If a source file is unreadable, log a warning and continue with remaining files.
- If topic classification is ambiguous for >3 files, pause and ask the user.
- If schema.md conflicts with discovered topics, surface the conflict and ask before updating.
- If a Hard Gate fails and cannot be auto-fixed, report the issue and continue with remaining checks.
