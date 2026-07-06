---
name: add-rose-meaning
description: Add or edit a rose count-meaning entry in the normalized data set (data/rose_meaning.csv + data/meaning_variants.csv) without breaking PK/FK integrity or the quiz pool. Use when the user wants to add a new バラの本数, add/change a 花言葉, or toggle whether a count is quizzable.
---

# Add / edit a rose meaning

The data is split across two related tables. A single logical "本数の花言葉"
touches **both** files, and the relational invariants must survive the edit.

## Tables

- `data/rose_meaning.csv` — `id,count,quiz_enabled,description`
  - `id`: surrogate PK. Assign the **next unused integer**; never reuse or re-number.
  - `count`: the number of roses. UNIQUE natural key.
  - `quiz_enabled`: `true` to include in the quiz pool, `false` to keep it
    collection-only (used to resolve near-duplicate meanings — see design doc §要決定2).
  - `description`: 解説文 shown on the collection card.
- `data/meaning_variants.csv` — `id,rose_meaning_id,sort_order,is_primary,meaning`
  - One row **per single meaning** (1NF). A count with two meanings gets two rows.
  - `rose_meaning_id`: FK → `rose_meaning.id`.
  - `sort_order`: `1..n`; `is_primary=true` for exactly one (the `sort_order=1` row).
  - `meaning`: a **single** value. Never put `/` or multiple meanings in one cell.

## Procedure to add a new count

1. Pick the next `id` for `rose_meaning.csv` (max existing id + 1).
2. Append the master row: `<id>,<count>,<true|false>,<description>`.
3. For each 花言葉 of that count, append a row to `meaning_variants.csv` with a
   new variant `id` (max existing + 1), the master `id` as `rose_meaning_id`,
   `sort_order` 1,2,…, and `is_primary=true` only on the first.
4. **Quiz-pool check**: if any meaning of the new count duplicates (exactly or
   near-identically) a meaning of an existing `quiz_enabled=true` count, set one
   side's `quiz_enabled=false` so pattern-A answers stay unique.
5. Run the validator and fix any error before committing:
   ```bash
   python3 .claude/skills/validate-rose-data/validate.py data
   ```

## Procedure to edit / remove

- **Edit a meaning**: change the `meaning` cell only; keep ids stable.
- **Remove a count**: delete its `rose_meaning` row **and all** its
  `meaning_variants` rows. Leave the `id` retired (do not renumber others).

Always finish by running `validate-rose-data`.
