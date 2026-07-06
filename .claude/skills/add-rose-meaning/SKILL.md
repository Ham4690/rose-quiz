---
name: add-rose-meaning
description: Add or edit a rose count-meaning entry in data/rose_meaning.csv without breaking PK/natural-key integrity or the quiz pool. Use when the user wants to add a new バラの本数, add/change a 花言葉, or toggle whether a count is quizzable.
---

# Add / edit a rose meaning

All rose data lives in a single master table, `data/rose_meaning.csv`. A logical
"本数の花言葉" is one row. The relational invariants must survive every edit.

## Table

`data/rose_meaning.csv` — `id,count,quiz_enabled,meaning,description`

- `id`: surrogate PK. Assign the **next unused integer**; never reuse or re-number.
- `count`: the number of roses. UNIQUE natural key.
- `quiz_enabled`: `true` to include in the quiz pool, `false` to keep it
  collection-only (used to resolve near-duplicate meanings — see `docs/design.md` §要決定2).
- `meaning`: the **single representative** 花言葉 (1NF — atomic, no `/`).
- `description`: 解説文 shown on the collection card.

> The source data had some counts with several meanings in one cell
> (`一目ぼれ / あなたしかいない`). We keep only the representative one per count.

## Procedure to add a new count

1. Pick the next `id` (max existing id + 1).
2. Append the row: `<id>,<count>,<true|false>,<meaning>,<description>`.
   - `meaning` must be a single value (no `/`).
3. **Quiz-pool check**: if the new meaning duplicates (exactly or near-identically)
   the meaning of an existing `quiz_enabled=true` count, set one side's
   `quiz_enabled=false` so pattern-A answers stay unique.
4. Run the validator and fix any error before committing:
   ```bash
   python3 .claude/skills/validate-rose-data/validate.py data
   ```

## Procedure to edit / remove

- **Edit a meaning**: change the `meaning` cell only; keep `id`/`count` stable.
  Re-check the quiz-pool uniqueness rule.
- **Remove a count**: delete its row. Leave the `id` retired (do not renumber others).

Always finish by running `validate-rose-data`.
