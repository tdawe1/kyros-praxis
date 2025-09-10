#!/usr/bin/env python3
import argparse
import csv
import os
import re
from collections import OrderedDict
from pathlib import Path


def norm_title(t: str) -> str:
    if t is None:
        return ""
    return re.sub(r"\s+", " ", t).strip().lower()


def read_csv_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    return headers, rows


def dedupe_by_title(rows_with_src):
    best = OrderedDict()
    for src_index, row in rows_with_src:
        key = norm_title(row.get("Title", ""))
        if not key:
            continue
        if key not in best:
            best[key] = (src_index, row)
            continue
        cur_index, cur_row = best[key]
        cur_ok = str(cur_row.get("Accepted", "")).strip().lower() == "yes"
        new_ok = str(row.get("Accepted", "")).strip().lower() == "yes"
        if new_ok and not cur_ok:
            best[key] = (src_index, row)
    return best


def write_csv(path: Path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_md(path: Path, counts, items):
    lines = ["# Deduplicated Tasks", "", f"- Source A: {counts[0]} rows", f"- Source B: {counts[1]} rows", f"- Unique (by Title): {len(items)} rows", "", "## Tasks", ""]
    for _, row in items:
        title = (row.get("Title", "") or "").strip()
        tid = (row.get("ID", "") or "").strip()
        pr = (row.get("Priority", "") or "").strip() or "P?"
        due = (row.get("Due", "") or "").strip() or "N/A"
        st = (row.get("Status", "") or "").strip() or "Status N/A"
        lines.append(f"- {title} ({tid}) — {st}, {pr}, Due: {due}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_plan(plan_path: Path, md_path: Path):
    content = md_path.read_text(encoding="utf-8")
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(content, encoding="utf-8")


def main():
    here = Path(__file__).resolve()
    base = here.parents[1]  # kyros-praxis/
    docs = base / "docs"
    default_srcs = [
        docs / "Tasks 2682b55f8d8581329b89d0635643317c_all.csv",
        docs / "Untitled 2682b55f8d8580bcaccaf5b744a95465.csv",
    ]
    parser = argparse.ArgumentParser(description="Sync deduped tasks and PLAN.md")
    parser.add_argument("--src", action="append", type=Path, default=default_srcs)
    parser.add_argument("--out-csv", type=Path, default=docs / "tasks_deduped.csv")
    parser.add_argument("--out-md", type=Path, default=docs / "tasks_deduped.md")
    parser.add_argument(
        "--plan",
        type=Path,
        default=Path(os.environ.get("PLAN_PATH", str(Path.home() / ".kilocode/rules/PLAN.md"))),
        help="Destination PLAN.md path",
    )
    parser.add_argument("--no-write-plan", action="store_true")
    args = parser.parse_args()

    headers = None
    rows_with_src = []
    counts = []
    for i, src in enumerate(args.src):
        h, r = read_csv_rows(src)
        if headers is None:
            headers = h
        counts.append(len(r))
        for row in r:
            rows_with_src.append((i, row))

    best = dedupe_by_title(rows_with_src)
    rows = [row for _, row in best.values()]
    write_csv(args.out_csv, headers, rows)
    write_md(args.out_md, counts, list(best.values()))
    if not args.no_write_plan:
        update_plan(args.plan, args.out_md)


if __name__ == "__main__":
    main()

