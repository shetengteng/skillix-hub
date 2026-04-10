# Command: kc init

Initialize a knowledge base in the current directory or a specified path.

## Usage

```
kc init                    # init in current directory
kc init --path <dir>       # init in specified directory
```

---

## Step 1 — Check Existing Config

Check if `.kc-config.json` already exists in the target directory.

- **Found:** Ask the user: "Knowledge base config already exists. Reinitialize? This will NOT delete existing raw/ or wiki/ content. (y/n)"
  - If no: print current config summary and stop.
  - If yes: continue, overwrite config only.
- **Not found:** Continue to Step 2.

---

## Step 2 — Scan for Existing Markdown

Look for existing `.md` files in the target directory:

```bash
find <target> -name "*.md" -not -path "*/node_modules/*" -not -path "*/.git/*" | head -20
```

If markdown files are found, present candidates:
```
Found markdown in: docs/, design/, notes/
Which directories should be knowledge sources? (comma-separated, or "all")
Default: [raw/designs, raw/decisions, raw/research, raw/notes]
```

If user picks existing directories (e.g. `design/`), use those as sources. Otherwise create the default `raw/` structure.

---

## Step 3 — Create Directory Structure

Create the raw/ and wiki/ directories:

```
{target}/
├── raw/
│   ├── designs/
│   ├── decisions/
│   ├── research/
│   └── notes/
└── wiki/
    └── concepts/
```

Skip creating any directory that already exists.

---

## Step 4 — Generate Config

Write `.kc-config.json`:

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

If the user selected custom source directories in Step 2, use those instead of the defaults.

---

## Step 5 — Ask Session Mode

```
How should AI use this knowledge base in conversations?
  [1] staging     — supplementary reference, check wiki when needed (default)
  [2] recommended — read wiki first, then raw files for depth
  [3] primary     — wiki is the main source, only check raw/ for low-coverage sections
```

Update `session_mode` in the config based on user choice.

---

## Step 6 — Create Wiki Scaffolds

Create empty scaffold files:

**wiki/INDEX.md:**
```markdown
# Wiki Index

> Auto-maintained by knowledge-compiler. Run `kc compile` to build.

No topics compiled yet. Add sources to raw/ and run `kc compile`.
```

**wiki/log.md:**
```markdown
# Compilation Log

> Append-only log of compilation runs.
```

---

## Step 7 — Report

Print:
```
Knowledge base initialized.

Sources: raw/designs/, raw/decisions/, raw/research/, raw/notes/
Output:  wiki/
Mode:    recommended

Next steps:
  1. Add materials to raw/ subdirectories
  2. Run: kc compile
```
