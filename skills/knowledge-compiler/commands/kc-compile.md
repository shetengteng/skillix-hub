# Command: kc compile

Trigger wiki compilation. Delegates to the `wiki-compiler` skill.

## Usage

```
kc compile                    # incremental — only recompile changed topics
kc compile --full             # full recompile of all topics
kc compile --topic <slug>     # recompile a single topic
kc compile --dry-run          # preview what would change, no writes
```

---

## Steps

1. **Verify config.** Check that `.kc-config.json` exists. If not: "No knowledge base found. Run `kc init` first."

2. **Parse flags** from the user's invocation:
   - No flags → incremental mode
   - `--full` → full recompile
   - `--topic <slug>` → single topic mode
   - `--dry-run` → preview only

3. **Read the compilation skill.** Load [skills/wiki-compiler.md](../skills/wiki-compiler.md) and execute the 5-phase pipeline with the parsed flags.

4. **Report results** after compilation completes:
   ```
   Compiled: 3 topics updated, 1 new, 12 unchanged
   Hard Gates: all passed
   Soft Gates: 2 warnings (see wiki/log.md)
   Wiki: wiki/INDEX.md
   ```

---

## Notes

- Incremental mode is the default and recommended for regular use.
- Use `--full` after major reorganization of raw/ files or after manually editing schema.md.
- Use `--dry-run` to preview before a large compilation.
- The compilation pipeline is defined in [skills/wiki-compiler.md](../skills/wiki-compiler.md) — read that file for the detailed 5-phase process.
