---
id: "{{topic-slug}}"
title: "{{Topic Title}}"
tags: [{{tag1}}, {{tag2}}]
sources:
  - {{raw/path/to/source.md}}
relations:
  related: []
  depends_on: []
created: "{{YYYY-MM-DD}}"
updated: "{{YYYY-MM-DD}}"
compile_count: 1
---

# {{Topic Title}}

> One-sentence definition or summary of this topic.

<!-- coverage: high | medium | low -->
<!-- Assign a coverage tag to each section below. -->
<!-- high = multiple consistent sources; medium = single source; low = inferred/sparse -->

## Summary
<!-- coverage: ? -->

A concise overview (3-6 sentences). What is this? Why does it matter? Where does it fit?

## Key Decisions
<!-- coverage: ? -->

Important design decisions, trade-offs, or architectural choices.

- **Decision:** Why this approach was chosen over alternatives.
  [source: raw/path/to/source.md]

## Current State
<!-- coverage: ? -->

What is the current status? What is in production today?

## Gotchas
<!-- coverage: ? -->

Common pitfalls, non-obvious behaviors, or things that surprised practitioners.

## Open Questions
<!-- coverage: ? -->

Unresolved debates, active discussion areas, or things the compiler couldn't determine from sources.

## Related
- [[related-concept-slug]]

## Sources
{{#each sources}}
- [source: {{this}}]
{{/each}}
