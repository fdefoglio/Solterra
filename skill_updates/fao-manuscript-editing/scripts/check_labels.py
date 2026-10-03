#!/usr/bin/env python3
"""Verify label integrity between a source and an edited FAO manuscript.

Extracts every paragraph label `^[N]` (or bare `[N]` at line start) from both
files and reports whether the sequences are identical — the import-contract
gate that binds every pipeline phase.

Usage:
  python3 check_labels.py SOURCE.md EDITED.md
  python3 check_labels.py SOURCE.md EDITED.md --strict   # also compare '[N] ' formatting

Exit code 0 = identical; 1 = mismatch (diff is printed); 2 = usage error.
"""
import re
import sys

LABEL_RE = re.compile(r'^\[(\d+)\]')


def labels(path):
    seq = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = LABEL_RE.match(line)
            if m:
                seq.append(m.group(1))
    return seq


def main():
    argv = sys.argv[1:]
    strict = '--strict' in argv
    argv = [a for a in argv if a != '--strict']
    if len(argv) != 2:
        print(__doc__)
        return 2
    src, edited = (labels(p) for p in argv)
    if strict:
        with open(argv[0], encoding='utf-8') as f:
            src_fmt = [l[:l.index(']') + 2] for l in f if LABEL_RE.match(l)]
        with open(argv[1], encoding='utf-8') as f:
            ed_fmt = [l[:l.index(']') + 2] for l in f if LABEL_RE.match(l)]
    else:
        src_fmt = ed_fmt = None

    ok = src == edited and (not strict or src_fmt == ed_fmt)
    print(f"{argv[0]}: {len(src)} labels")
    print(f"{argv[1]}: {len(edited)} labels")
    if ok:
        print("LABEL SEQUENCES IDENTICAL")
        return 0
    print("LABEL MISMATCH")
    for i, (a, b) in enumerate(zip(src, edited)):
        if a != b:
            print(f"  first divergence at position {i}: source [{a}] vs edited [{b}]")
            break
    if len(src) != len(edited):
        print(f"  length differs: {len(src)} vs {len(edited)}")
        longer = src if len(src) > len(edited) else edited
        missing = longer[min(len(src), len(edited)):]
        print(f"  extra labels in {'source' if longer is src else 'edited'}: "
              f"{missing[:20]}{' ...' if len(missing) > 20 else ''}")
    if strict and src_fmt != ed_fmt:
        print("  '[n] ' formatting differs between source and edited")
    return 1


if __name__ == '__main__':
    sys.exit(main())
