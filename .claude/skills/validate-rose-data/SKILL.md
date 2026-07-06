---
name: validate-rose-data
description: Validate the normalized rose-quiz CSV data set under data/ (PK uniqueness, FK integrity, 1NF, quiz-pool answer uniqueness, title score coverage). Use before committing any change to data/rose_meaning.csv, data/meaning_variants.csv, or data/quiz_titles.csv.
---

# Validate rose-quiz data

The CSVs in `data/` are the confirmed master (source of truth). They model a
normalized relational schema even though the app ships as a static frontend, so
they must stay RDB-consistent at all times.

## When to use

Run this whenever you add/edit/reorder rows in any of:

- `data/rose_meaning.csv` — master (`id` PK, `count` natural key, `quiz_enabled`, `description`)
- `data/meaning_variants.csv` — 1NF split of meanings (`id` PK, `rose_meaning_id` FK)
- `data/quiz_titles.csv` — result-screen title bands

## How to run

```bash
python3 .claude/skills/validate-rose-data/validate.py data
```

Exit code 0 = all invariants hold; 1 = violations printed as `ERROR ...`.

## Invariants enforced

1. **rose_meaning**: `id` unique; `count` unique (natural key); `quiz_enabled ∈ {true,false}`; non-empty `description`.
2. **meaning_variants**: `id` unique; every `rose_meaning_id` resolves to a `rose_meaning.id`; exactly one `is_primary=true` per parent; `sort_order` contiguous `1..n`; no `/` left in a `meaning` cell (1NF); every master row has ≥1 variant.
3. **Quiz pool (pattern A)**: among `quiz_enabled=true` rows, no meaning string is shared by two different counts — otherwise a 4-choice "本数→意味" question would have a non-unique correct answer. Near-duplicate (fuzzy) pairs are resolved by disabling one side via `quiz_enabled=false`; see `docs/design.md` §要決定2.
4. **quiz_titles**: score bands `[min_correct, max_correct]` cover `0..5` contiguously with no gaps or overlaps.

## Important

`id` is a stable surrogate key. **Never re-number `id`s to close a gap** — FKs in
`meaning_variants` point at them. When you delete a master row, delete its
variants too and leave the `id` retired. Adding a row uses the next unused `id`.
