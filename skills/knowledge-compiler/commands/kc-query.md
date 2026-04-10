# Command: kc query

Query the wiki to answer a question. Uses INDEX.md as the entry point, reads relevant topic articles, and synthesizes an answer with citations.

## Usage

```
kc query <question>
kc query <question> --save       # save the answer to wiki/analyses/
```

---

## Steps

1. **Verify config.** Check that `.kc-config.json` exists and `wiki/INDEX.md` has content. If wiki is empty: "No compiled wiki found. Run `kc compile` first."

2. **Read INDEX.md** to identify relevant topics for the question.

3. **Read the topic articles** for those topics (`wiki/concepts/{slug}.md`).

4. **Check coverage tags.** If a section relevant to the question has coverage tag `low`, also read the cited raw source files for that section to get more detail.

5. **Synthesize an answer** with citations:
   - Wiki citations: `[wiki: wiki/concepts/topic-slug.md]`
   - Raw source citations: `[source: raw/designs/foo.md]`

6. **Optionally save.** If `--save` flag is set, or the answer involved significant synthesis across multiple topics, ask:
   "This answer looks worth keeping. Save to `wiki/analyses/`? (y/n)"

   If yes:
   - Create `wiki/analyses/{YYYY-MM-DD}-{question-slug}.md` with the answer content.
   - Add an entry to the Analyses section of `wiki/INDEX.md`.

7. **Log.** Append to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] query | <question summary>
   ```

---

## Notes

- The query command leverages the coverage tags to decide how deep to go: high-coverage sections are trusted directly, low-coverage sections trigger a raw/ file lookup.
- Saved analyses become part of the wiki and can be referenced by future queries.
