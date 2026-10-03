#!/usr/bin/env python3
"""Repair double-encoded UTF-8 (mojibake) in FAO project assets.

The files were written by decoding UTF-8 bytes as cp1252/latin-1 and re-encoding
as UTF-8, so 'Côte' became 'CÃ´te'. This reverses that transform on the affected
substrings only, leaving correctly-encoded text untouched.
"""
import re, sys, shutil, unicodedata
from pathlib import Path

# Characters that appear in cp1252-mojibake tails
TAIL = ('\x80-\xBF\u0080-\u00FF\u2013\u2014\u2018\u2019\u201A\u201C\u201D\u201E'
        '\u2020\u2021\u2022\u2026\u2030\u2039\u203A\u20AC\u2122\u0152\u0153'
        '\u0160\u0161\u0178\u017D\u017E\u0192\u02C6\u02DC')
PAT = re.compile(r'(?:[\u00C2\u00C3\u00E2\u00C5\u00C4][' + TAIL + r']{1,3})+')

def repair(text):
    def sub(m):
        s = m.group(0)
        for enc in ('cp1252', 'latin-1'):
            try:
                return s.encode(enc).decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
        return s
    prev = None
    while prev != text:                 # iterate for triple-encoded cases
        prev, text = text, PAT.sub(sub, text)
    return text

RESIDUAL = re.compile(r'[\u00C3\u00C2][\x80-\xBF]|\u00E2\u20AC')

def main(paths, outdir, backup=None):
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in map(Path, paths):
        src = p.read_text(encoding='utf-8')
        dst = repair(src)
        if backup and dst != src:
            shutil.copy2(p, Path(backup) / (p.name + '.orig'))
        (out / p.name).write_text(dst, encoding='utf-8')
        rows.append((p.name, len(RESIDUAL.findall(src)), len(RESIDUAL.findall(dst)),
                     'changed' if dst != src else 'clean'))
    w = max(len(r[0]) for r in rows)
    print(f"{'file'.ljust(w)}  before  after  status")
    for n, b, a, s in rows:
        print(f"{n.ljust(w)}  {b:>6}  {a:>5}  {s}")
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[2:], sys.argv[1]))
