#!/usr/bin/env python3
"""
Validate the rose-quiz data set (data/*.csv).

Checks the relational invariants that must hold for the CSV master to be a
faithful, RDB-ready source of truth:

  rose_meaning : surrogate PK unique, `count` natural key unique,
                 quiz_enabled is boolean, `meaning` atomic (1NF, single value),
                 non-empty meaning/description
  quiz pool (A): among quiz_enabled=true rows, no two counts share an identical
                 meaning (would make a 4-choice "本数→意味" answer non-unique)
  quiz_titles  : exactly one title per score 0..MAX_SCORE (1:1, no gap/dup)

Exit code 0 = all invariants hold, 1 = at least one violation.
Usage: python3 .claude/skills/validate-rose-data/validate.py [data_dir]
"""
import csv
import sys
from pathlib import Path

MAX_SCORE = 5  # a quiz round is 5 questions

def load(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main(data_dir):
    data = Path(data_dir)
    errors = []

    master = load(data / "rose_meaning.csv")
    titles = load(data / "quiz_titles.csv")

    # ---- rose_meaning ----
    ids, counts = set(), set()
    for r in master:
        rid, cnt = r["id"], r["count"]
        if rid in ids:
            errors.append(f"rose_meaning: duplicate id {rid}")
        ids.add(rid)
        if cnt in counts:
            errors.append(f"rose_meaning: duplicate count {cnt} (natural key must be UNIQUE)")
        counts.add(cnt)
        if r["quiz_enabled"] not in ("true", "false"):
            errors.append(f"rose_meaning id={rid}: quiz_enabled must be true/false, got {r['quiz_enabled']!r}")
        if not r["meaning"].strip():
            errors.append(f"rose_meaning id={rid}: empty meaning")
        if "/" in r["meaning"]:
            errors.append(f"rose_meaning id={rid}: 1NF violation, '/' in meaning {r['meaning']!r} "
                          f"(keep a single representative meaning per count)")
        if not r["description"].strip():
            errors.append(f"rose_meaning id={rid}: empty description")

    # ---- quiz pool (pattern A uniqueness) ----
    meaning_owner = {}  # meaning -> set of enabled counts using it
    for r in master:
        if r["quiz_enabled"] == "true":
            meaning_owner.setdefault(r["meaning"].strip(), set()).add(r["count"])
    for m, owners in meaning_owner.items():
        if len(owners) > 1:
            errors.append(f"quiz pool: meaning {m!r} shared by enabled counts {sorted(owners, key=int)} "
                          f"-> pattern-A answer non-unique")

    # ---- quiz_titles (one title per score 0..MAX_SCORE) ----
    covered = {}
    for t in titles:
        s = int(t["correct"])
        if not (0 <= s <= MAX_SCORE):
            errors.append(f"quiz_titles id={t['id']}: correct {s} out of range 0..{MAX_SCORE}")
        if s in covered:
            errors.append(f"quiz_titles: score {s} mapped by more than one title")
        covered[s] = t
        if not t["title"].strip():
            errors.append(f"quiz_titles id={t['id']}: empty title")
    for s in range(0, MAX_SCORE + 1):
        if s not in covered:
            errors.append(f"quiz_titles: score {s} has no title")

    # ---- report ----
    enabled = sum(1 for r in master if r["quiz_enabled"] == "true")
    print(f"rose_meaning: {len(master)} rows ({enabled} quiz-enabled)")
    print(f"quiz_titles: {len(titles)} titles (1:1 with scores 0..{MAX_SCORE})")
    if errors:
        print(f"\nFAILED with {len(errors)} error(s):")
        for e in errors:
            print(f"  ERROR {e}")
        return 1
    print("\nOK: all relational invariants hold.")
    return 0

if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "data"
    sys.exit(main(d))
