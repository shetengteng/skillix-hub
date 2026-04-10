# Command: kc add

Add source material to the knowledge base.

## Usage

```
kc add <path>                          # add a single file
kc add <path> --tags "tag1,tag2"       # add with tags
kc add <directory> --recursive         # add all .md files in directory
```

---

## Steps

1. **Verify config.** Check that `.kc-config.json` exists. If not: "No knowledge base found. Run `kc init` first."

2. **Determine target location.** Based on the file content, suggest which `raw/` subdirectory to place it in:
   - Design docs, architecture docs → `raw/designs/`
   - Decision records, ADRs → `raw/decisions/`
   - Research, papers, technical investigations → `raw/research/`
   - Meeting notes, personal notes → `raw/notes/`
   - Ask the user to confirm or override: "Place in `raw/designs/`? (y/n/custom path)"

3. **Copy or symlink.** Copy the file into the determined raw/ subdirectory.
   - If the file is already inside `raw/`, skip the copy — just acknowledge it.
   - If `--recursive`, walk the directory and copy all `.md` files, preserving subdirectory structure.

4. **Report:**
   ```
   Added: raw/designs/api-gateway-design.md
   Tags: architecture, api
   Run `kc compile` to include in wiki.
   ```

---

## Notes

- Raw files are immutable by convention — the compiler never modifies files in `raw/`.
- Tags are stored as a comment at the top of the copied file if not already present: `<!-- tags: tag1, tag2 -->`.
- Adding files does NOT trigger compilation. The user must run `kc compile` separately.
