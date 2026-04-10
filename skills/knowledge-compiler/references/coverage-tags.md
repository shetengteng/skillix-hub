# Coverage Tags Reference

Coverage tags are the core mechanism for tracking how well each section of a concept article is supported by source material. They guide both human readers and AI agents on when to trust the wiki versus when to verify against raw sources.

---

## Tag Definitions

### high

```markdown
<!-- coverage: high -->
```

**Meaning:** Multiple consistent sources confirm this information. The synthesis is well-supported.

**When to assign:**
- 2+ source files provide consistent information on this section
- The sources are authoritative (design docs, official decisions, reviewed research)
- No conflicting information exists across sources

**AI behavior:** Trust and cite directly. No need to cross-reference raw/ files.

**Reader behavior:** Information is reliable. Treat as established fact within this knowledge base.

### medium

```markdown
<!-- coverage: medium -->
```

**Meaning:** Single source or partial coverage. The information is likely correct but not cross-validated.

**When to assign:**
- Only 1 source file covers this section
- Multiple sources exist but they only partially overlap
- The source is a meeting note or informal document (lower authority than a design doc)

**AI behavior:** Cite with a note that the information may need supplementation. If the user asks follow-up questions on a medium section, consider reading the raw source file for more context.

**Reader behavior:** Useful but verify if making critical decisions based on this.

### low

```markdown
<!-- coverage: low -->
```

**Meaning:** Inferred, sparse, or minimally supported. The compiler synthesized this from indirect references or fragmentary information.

**When to assign:**
- No source directly discusses this section's topic
- Information was inferred from context in other sections or related topics
- The source material is outdated or tangentially related
- The section was created as a placeholder to maintain article structure

**AI behavior:** Before citing or using this section's content, read the raw source files listed in the article's frontmatter `sources` field. If sources don't help, flag as uncertain.

**Reader behavior:** Treat as a starting point, not a conclusion. Verify before acting.

---

## Placement Rules

1. Every `## Section` heading must be immediately followed by a coverage tag on the next line:
   ```markdown
   ## Summary
   <!-- coverage: high -->

   Content here...
   ```

2. The tag applies to all content under that section until the next `##` heading.

3. Sub-sections (`###`) inherit their parent section's coverage unless explicitly overridden.

4. The article-level coverage (shown in INDEX.md) is the **dominant** tag — the most common coverage level across all sections. Ties break toward the lower level.

---

## Coverage in Session Mode

The `session_mode` in `.kc-config.json` interacts with coverage tags:

| Mode | high sections | medium sections | low sections |
|------|--------------|----------------|-------------|
| **staging** | Read if asked | Read if asked | Read if asked |
| **recommended** | Read wiki first | Read wiki, note uncertainty | Read wiki + raw sources |
| **primary** | Wiki only | Wiki only, flag uncertainty | Read raw sources |

---

## Upgrading Coverage

Coverage improves when:
- More sources are added to `raw/` covering the same topic
- The compiler detects consistent information across multiple sources
- A user manually upgrades a tag after verifying content

Coverage is recalculated during `kc compile`. Manual overrides by the user are preserved — the compiler will not downgrade a tag that a user has manually set to a higher level.
