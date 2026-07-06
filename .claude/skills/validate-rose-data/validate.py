#!/usr/bin/env python3
"""
Validate the normalized rose-quiz data set (data/*.csv).

Checks the relational invariants that must hold for the CSV master to be a
faithful, RDB-ready source of truth:

  rose_meaning      : surrogate PK unique, `count` natural key unique,
                      quiz_enabled is boolean, description non-empty
  meaning_variants  : PK unique, FK -> rose_meaning.id valid, exactly one
                      is_primary per parent, sort_order 1..n contiguous,
                      1NF (no "/" left in a single meaning cell)
  quiz pool (A)     : among quiz_enabled=true rows, no two counts share an
                      identical meaning (would make a 4-choice answer non-unique)
  quiz_titles       : score bands cover 0..MAX_SCORE contiguously, no overlap

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
    errors, warnings = [], []

    master = load(data / "rose_meaning.csv")
    variants = load(data / "meaning_variants.csv")
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
        if not r["description"].strip():
            errors.append(f"rose_meaning id={rid}: empty description")

    # ---- meaning_variants ----
    vids = set()
    by_parent = {}
    for v in variants:
        vid, fk = v["id"], v["rose_meaning_id"]
        if vid in vids:
            errors.append(f"meaning_variants: duplicate id {vid}")
        vids.add(vid)
        if fk not in ids:
            errors.append(f"meaning_variants id={vid}: FK rose_meaning_id={fk} has no matching rose_meaning.id")
        if not v["meaning"].strip():
            errors.append(f"meaning_variants id={vid}: empty meaning")
        if "/" in v["meaning"]:
            errors.append(f"meaning_variants id={vid}: 1NF violation, '/' still present in meaning {v['meaning']!r}")
        by_parent.setdefault(fk, []).append(v)

    for fk, vs in by_parent.items():
        primaries = [v for v in vs if v["is_primary"] == "true"]
        if len(primaries) != 1:
            errors.append(f"rose_meaning_id={fk}: must have exactly one is_primary variant, found {len(primaries)}")
        orders = sorted(int(v["sort_order"]) for v in vs)
        if orders != list(range(1, len(vs) + 1)):
            errors.append(f"rose_meaning_id={fk}: sort_order not contiguous 1..n, got {orders}")

    # every master row should have at least one variant
    for rid in ids:
        if rid not in by_parent:
            errors.append(f"rose_meaning id={rid}: has no meaning_variants")

    # ---- quiz pool (pattern A uniqueness) ----
    enabled_ids = {r["id"] for r in master if r["quiz_enabled"] == "true"}
    meaning_owner = {}  # meaning -> count(s) among enabled rows
    count_by_id = {r["id"]: r["count"] for r in master}
    for v in variants:
        if v["rose_meaning_id"] in enabled_ids:
            m = v["meaning"].strip()
            meaning_owner.setdefault(m, set()).add(count_by_id[v["rose_meaning_id"]])
    for m, owners in meaning_owner.items():
        if len(owners) > 1:
            errors.append(f"quiz pool: meaning {m!r} shared by enabled counts {sorted(owners, key=int)} "
                          f"-> pattern-A answer non-unique")

    # ---- quiz_titles ----
    covered = set()
    for t in titles:
        lo, hi = int(t["min_correct"]), int(t["max_correct"])
        if lo > hi:
            errors.append(f"quiz_titles id={t['id']}: min_correct {lo} > max_correct {hi}")
        for s in range(lo, hi + 1):
            if s in covered:
                errors.append(f"quiz_titles: score {s} covered by more than one band")
            covered.add(s)
    for s in range(0, MAX_SCORE + 1):
        if s not in covered:
            errors.append(f"quiz_titles: score {s} not covered by any title band")

    # ---- report ----
    print(f"rose_meaning: {len(master)} rows ({len(enabled_ids)} quiz-enabled)")
    print(f"meaning_variants: {len(variants)} rows")
    print(f"quiz_titles: {len(titles)} bands covering 0..{MAX_SCORE}")
    for w in warnings:
        print(f"WARN  {w}")
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
