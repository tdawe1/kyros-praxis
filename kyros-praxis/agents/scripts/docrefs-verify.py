#!/usr/bin/env python3
# scripts/docrefs-verify.py — verify DocRef ids in code map to DOC_INDEX.txt
import re, sys, os, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOC_INDEX = ROOT / "docs" / "DOC_INDEX.txt"

def load_index():
    idx = {}
    if not DOC_INDEX.exists():
        print("DOC_INDEX not found", file=sys.stderr); sys.exit(2)
    for line in DOC_INDEX.read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if not line or line.startswith("#"): continue
        if "=" in line:
            k,v = line.split("=",1); idx[k.strip()] = v.strip()
    return idx

def find_docrefs():
    refs = []
    for path in ROOT.rglob("*"):
        if path.is_dir(): continue
        if any(s in path.parts for s in [".git",".venv","node_modules",".pytest_cache","dist","build",".next"]): continue
        try:
            txt = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in re.finditer(r"DocRef:\s*([a-zA-Z0-9\-_.]+)", txt):
            refs.append((path, m.group(1)))
    return refs

def main():
    idx = load_index()
    missing = []
    for path, rid in find_docrefs():
        if rid not in idx:
            missing.append((str(path), rid))
    if missing:
        print("Missing DocIDs:", file=sys.stderr)
        for p,r in missing:
            print(f"  {p}: DocRef {r} not found in DOC_INDEX.txt", file=sys.stderr)
        sys.exit(1)
    print("DocRefs OK")
if __name__ == "__main__":
    main()
