---
title: Wiki Schema
updated: "{{YYYY-MM-DD}}"
---

# Wiki Schema

> This file is the structural contract for this knowledge base. It is co-maintained by the compiler and the user.
> The compiler reads this file to guide topic naming, categorization, and cross-reference rules.
> Edit this file to override compiler defaults.

## Topic Taxonomy

Define the top-level categories and the topics that belong to each.

### {{Category Name}}
- `{{topic-slug}}` — one-line description

### Uncategorized
<!-- New topics without a clear category appear here. Move them as taxonomy matures. -->

## Naming Conventions

- Topic slugs: `lowercase-kebab-case`
- Prefer specific over generic: `transformer-attention` not `attention`
- Avoid year suffixes unless the year is load-bearing: `gpt-4` ok, `llm-2024` not ok

## Cross-Reference Rules

Define which topics should always link to each other:

```
<!-- example:
transformer-architecture <-> attention-mechanism
retrieval-augmented-generation -> vector-database
fine-tuning -> parameter-efficient-training
-->
```

## Deprecated Topics

Topics that have been merged or renamed. The compiler will not recreate these.

| Old Slug | Merged Into | Date |
|----------|-------------|------|

## Notes

Free-form notes about the wiki structure that don't fit above.
