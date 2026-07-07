---
name: validate-rose-data
description: Validate the rose-quiz CSV data set under data/ (PK uniqueness, natural-key uniqueness, 1NF atomic meaning, quiz-pool answer uniqueness, title score coverage). Use before committing any change to data/rose_meaning.csv or data/quiz_titles.csv.
---

# Validate rose-quiz data

The CSVs in `data/` are the confirmed master (source of truth). They model a
normalized relational schema even though the app ships as a static frontend, so
they must stay RDB-consistent at all times.

## When to use

Run this whenever you add/edit/reorder rows in either of:

- `data/rose_meaning.csv` — master (`id` PK, `count` natural key, `quiz_enabled`, `meaning`, `description`)
- `data/quiz_titles.csv` — result-screen title bands

## How to run

```bash
python3 .claude/skills/validate-rose-data/validate.py data
```

Exit code 0 = all invariants hold; 1 = violations printed as `ERROR ...`.

## Invariants enforced

1. **rose_meaning**: `id` unique; `count` unique (natural key); `quiz_enabled ∈ {true,false}`; non-empty `meaning` and `description`; `meaning` is a **single value** (no `/` — 1NF atomic; keep one representative 花言葉 per count).
2. **Quiz pool (pattern A)**: among `quiz_enabled=true` rows, no meaning string is shared by two different counts — otherwise a 4-choice "本数→意味" question would have a non-unique correct answer. Near-duplicate (fuzzy) pairs are resolved by disabling one side via `quiz_enabled=false`; see `docs/design.md` §要決定2.
3. **quiz_titles**: exactly one title per score (`correct` = 0..5), 1:1 with no gaps or duplicates.

## Important

`id` is a stable surrogate key. **Never re-number `id`s to close a gap** — treat
them as permanent identities (RDB-ready). When you delete a row, leave its `id`
retired; a new row uses the next unused `id`.
