# Quality Gates Reference

Detailed definitions of the Hard and Soft Gates used by `kc lint` and the compile pipeline's Phase 4 verification.

---

## Hard Gates

Hard Gates must pass. If a gate fails, attempt to fix it automatically. If auto-fix is not possible, report the failure and continue checking remaining gates.

### 1. Frontmatter Complete

**Check:** Every `wiki/concepts/*.md` file has YAML frontmatter with these required fields:
- `id` — topic slug (must match filename)
- `title` — human-readable title
- `sources` — list of raw/ file paths
- `created` — date of first compilation
- `updated` — date of last compilation

**Auto-fix:** Add missing fields with sensible defaults:
- `id`: derive from filename
- `title`: derive from H1 heading
- `sources`: `[]` (empty, flag for user attention)
- `created`/`updated`: today's date

### 2. Coverage Tags Present

**Check:** Every `## Section` heading in a concept article is followed by a `<!-- coverage: high|medium|low -->` comment.

**Auto-fix:** Add `<!-- coverage: low -->` to sections missing the tag.

### 3. Source References Valid

**Check:** Every `[source: raw/path/to/file.md]` citation in a concept article points to a file that actually exists in the filesystem.

**Auto-fix:** Remove the broken reference and add a warning comment: `<!-- WARNING: source removed, file not found: raw/old-path.md -->`. Downgrade the section's coverage to `low` if it was higher.

### 4. Schema Consistency

**Check:** Every topic that has a compiled article in `wiki/concepts/` appears in `wiki/schema.md` under some category.

**Auto-fix:** Add missing topics to the `### Uncategorized` section of schema.md.

### 5. Non-Empty Content

**Check:** Every section in a concept article has substantive content beyond the heading. A section with only the heading and coverage tag but no prose is considered empty.

**Auto-fix:** Insert `[NEEDS INPUT: no source content available for this section]` as a placeholder.

---

## Soft Gates

Soft Gates produce warnings but do not block compilation or lint from completing. They highlight areas that need attention.

### 1. Stale Articles

**Check:** Compare source file mtimes against `.compile-state.json`.
- A source file whose mtime is newer than the recorded mtime means the associated topic may be outdated.

**Severity:**
- Source changed <7 days ago: info
- Source changed 7-30 days ago: warning
- Source changed >30 days ago, or topic >30 days since `updated` date: alert

### 2. Orphan Pages

**Check:** Find wiki pages that have no inbound links:
- Not referenced in `wiki/INDEX.md`
- Not linked via `[[slug]]` from any other concept article

**Suggestion:** Consider linking from a related topic or removing if no longer relevant.

### 3. Missing Cross-References

**Check:** Scan concept article text for mentions of other topic titles or slugs that are not linked with `[[slug]]` notation.

**Suggestion:** Add `[[slug]]` links where topics are mentioned.

### 4. Low Coverage Clusters

**Check:** Flag topics where ALL sections have coverage tag `low`. These topics have minimal source support and may be unreliable.

**Suggestion:** Add more source materials to `raw/` covering this topic, then run `kc compile --topic <slug>`.

### 5. Content Contradictions

**Check:** Look for conflicting claims across different concept articles about the same subject. For example, if topic A says "we use PostgreSQL" and topic B says "we use MySQL" for the same system.

**Suggestion:** Review the conflicting articles and resolve. This check requires AI judgment — flag potential contradictions for user review.

### 6. Schema Drift

**Check:** Compare topics listed in `wiki/schema.md` against actual files in `wiki/concepts/`. Flag:
- Topics in schema but no article file
- Topics in articles but not in schema (also caught by Hard Gate 4)

### 7. Broken Wiki Links

**Check:** Find `[[slug]]` references in concept articles that point to non-existent pages (no matching `wiki/concepts/slug.md` file).

**Suggestion:** Create the missing topic or fix the link.

### 8. Missing Optional Frontmatter

**Check:** Pages lacking recommended but not required fields:
- `tags` — helps with search and categorization
- `relations.related` — helps with knowledge graph navigation
- `relations.depends_on` — clarifies dependency relationships

**Suggestion:** Add these fields to improve wiki navigability.
