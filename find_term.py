"""
find_term.py - which project folders mention a word or acronym?

Searches DOCX, XLSX, CSV, TSV and MD files under a root folder and reports,
per sub-folder, whether each term occurs, how often, and where.

DOCX: body, tables, text boxes, headers/footers (all variants), footnotes,
      endnotes, comments, tracked insertions (deleted text with --include-deleted)
XLSX: every sheet (also hidden ones), shared/inline strings, formula results,
      cell comments. Reports sheet and cell, e.g. Terms!B12
CSV/TSV/MD: plain text, reports line numbers

Matching ignores differences that are invisible in Word: non-breaking spaces,
curly vs straight quotes, soft hyphens, hyphen/dash variants.

Usage:
  python find_term.py VGGTs --root "P:\\manuscripts"
  python find_term.py VGGT --loose --root manuscripts       # VGGT, VGGTs, VGGT's
  python find_term.py VGGT --types xlsx --root manuscripts         # XLSX files only
  python find_term.py VGGT "foundation model" --root manuscripts   # several terms at once
  python find_term.py VGGT --root manuscripts --csv hits.csv       # full hit list for Excel

Options:
  --types LIST       only search these file types, e.g. --types xlsx  or  --types docx,xlsx
                     (default: docx,xlsx,csv,tsv,md)
  --case             case-sensitive (default: case-insensitive)
  --substring        also match inside longer words (default: whole word only)
  --loose            allow a trailing s / 's after the term
  --regex            treat terms as regular expressions
  --snippets N       snippets shown per term per file (default 2, 0 = none)
  --width N          characters of context on each side (default 40)

Exit status: 0 if any term was found, 1 if none, like grep.
"""

import argparse, csv, os, re, sys, zipfile
import xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
S = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
PKG_REL = '{http://schemas.openxmlformats.org/package/2006/relationships}'

# ---------- normalisation (mostly 1:1 so snippets stay readable) ----------

_NORM = {
    0x2018: "'", 0x2019: "'", 0x201A: "'", 0x201B: "'", 0x2032: "'",
    0x201C: '"', 0x201D: '"', 0x201E: '"', 0x201F: '"', 0x2033: '"',
    0x2010: '-', 0x2011: '-', 0x2012: '-', 0x2013: '-', 0x2212: '-',
    0x00AD: None, 0x200B: None, 0x200C: None, 0x200D: None, 0xFEFF: None,
}
for _c in (0x00A0, 0x2007, 0x202F, 0x2009, 0x200A, 0x2002, 0x2003, 0x3000):
    _NORM[_c] = ' '

def norm(s: str) -> str:
    return s.translate(_NORM)

# ---------- readers: each yields (location, text) ----------

def _para_text(p, include_deleted):
    out = []
    def walk(el):
        for ch in el:
            tag = ch.tag
            if tag == W + 'p' or tag in (W + 'pPr', W + 'rPr'):
                continue            # nested paragraphs (text boxes) are visited on their own
            if tag == W + 't' or (include_deleted and tag == W + 'delText'):
                out.append(ch.text or '')
            elif tag in (W + 'tab', W + 'br', W + 'cr'):
                out.append(' ')
            elif tag == W + 'noBreakHyphen':
                out.append('-')
            else:
                walk(ch)
    walk(p)
    return ''.join(out)

DOCX_PARTS = re.compile(r'^word/((?:document|header\d*|footer\d*|footnotes|endnotes|comments))\.xml$')

def read_docx(path, include_deleted=False):
    with zipfile.ZipFile(path) as z:
        for name in sorted(z.namelist()):
            m = DOCX_PARTS.match(name)
            if not m:
                continue
            label = m.group(1)
            root = ET.fromstring(z.read(name))
            for i, p in enumerate(root.iter(W + 'p'), 1):
                text = _para_text(p, include_deleted)
                if text.strip():
                    yield f'{label} para {i}', text

def _si_text(si):
    parts = []
    for ch in si:                   # skip phonetic runs (rPh)
        if ch.tag == S + 't':
            parts.append(ch.text or '')
        elif ch.tag == S + 'r':
            parts.extend(t.text or '' for t in ch.findall(S + 't'))
    return ''.join(parts)

def read_xlsx(path, include_deleted=False):
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())

        shared = []
        if 'xl/sharedStrings.xml' in names:
            root = ET.fromstring(z.read('xl/sharedStrings.xml'))
            shared = [_si_text(si) for si in root.iter(S + 'si')]

        # sheet name -> part path
        rels = {}
        if 'xl/_rels/workbook.xml.rels' in names:
            for rel in ET.fromstring(z.read('xl/_rels/workbook.xml.rels')).iter(PKG_REL + 'Relationship'):
                target = rel.get('Target', '').lstrip('/')
                rels[rel.get('Id')] = target if target.startswith('xl/') else 'xl/' + target
        sheets = []
        for sh in ET.fromstring(z.read('xl/workbook.xml')).iter(S + 'sheet'):
            part = rels.get(sh.get(R + 'id'))
            if part in names:
                sheets.append((sh.get('name'), part))

        for sheet_name, part in sheets:
            for _, c in ET.iterparse(z.open(part)):
                if c.tag != S + 'c':
                    continue
                t = c.get('t')
                v = c.find(S + 'v')
                if t == 's' and v is not None and v.text is not None:
                    text = shared[int(v.text)]
                elif t == 'inlineStr':
                    is_ = c.find(S + 'is')
                    text = _si_text(is_) if is_ is not None else ''
                elif v is not None and t != 'e':
                    text = v.text or ''
                else:
                    text = ''
                if text.strip():
                    yield f'{sheet_name}!{c.get("r")}', text
                c.clear()

        for name in sorted(n for n in names if re.match(r'^xl/comments\d*\.xml$', n)):
            for cm in ET.fromstring(z.read(name)).iter(S + 'comment'):
                text = ''.join(t.text or '' for t in cm.iter(S + 't'))
                if text.strip():
                    yield f'comment {cm.get("ref")}', text

def read_text(path, include_deleted=False):
    with open(path, 'rb') as f:
        raw = f.read()
    for enc in ('utf-8-sig', 'cp1252'):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            pass
    else:
        text = raw.decode('latin-1')
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip():
            yield f'line {i}', line

READERS = {'.docx': read_docx, '.xlsx': read_xlsx,
           '.csv': read_text, '.tsv': read_text, '.md': read_text}

# ---------- matching ----------

def build_pattern(term, args):
    body = term if args.regex else re.escape(norm(term))
    if args.loose:
        body += r"(?:'?s)?"
    if not args.substring:
        body = rf'(?<!\w)(?:{body})(?!\w)'
    return re.compile(body, 0 if args.case else re.IGNORECASE)

def snippet(text, m, width):
    a, b = max(0, m.start() - width), min(len(text), m.end() + width)
    return ('...' if a else '') + text[a:m.start()] + '**' + m.group() + '**' + text[m.end():b] + ('...' if b < len(text) else '')

# ---------- scan ----------

def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith('.'))
        for f in sorted(filenames):
            if not f.startswith(('~$', '.')):
                yield os.path.join(dirpath, f)

def group_of(root, path):
    parts = os.path.relpath(path, root).split(os.sep)
    return parts[0] if len(parts) > 1 else '(root)'

def scan(args):
    patterns = [(t, build_pattern(t, args)) for t in args.terms]
    hits = []                       # dicts: group, file, location, term, snippet
    files_per_group = {d: 0 for d in sorted(os.listdir(args.root))      # list every folder, even
                       if os.path.isdir(os.path.join(args.root, d)) and not d.startswith('.')}  # with 0 files searched
    skipped, errors = {}, []

    for path in iter_files(args.root):
        ext = os.path.splitext(path)[1].lower()
        group = group_of(args.root, path)
        if ext.lstrip('.') not in args.types_set and ext in READERS:
            continue                # supported type, but not requested via --types
        if ext not in READERS:
            skipped[ext or '(none)'] = skipped.get(ext or '(none)', 0) + 1
            continue
        files_per_group[group] = files_per_group.get(group, 0) + 1
        rel = os.path.relpath(path, args.root)
        try:
            for loc, text in READERS[ext](path, include_deleted=args.include_deleted):
                ntext = norm(text)
                for term, pat in patterns:
                    for m in pat.finditer(ntext):
                        hits.append(dict(group=group, file=rel, location=loc, term=term,
                                         snippet=snippet(ntext, m, args.width)))
        except Exception as e:
            errors.append((rel, f'{type(e).__name__}: {e}'))
    return hits, files_per_group, skipped, errors

# ---------- report ----------

def print_report(args, hits, files_per_group, skipped, errors):
    groups = sorted(files_per_group)
    cell = {}
    for h in hits:
        c = cell.setdefault((h['group'], h['term']), [0, set()])
        c[0] += 1
        c[1].add(h['file'])

    head = ['Folder', 'Files'] + args.terms
    rows = []
    for g in groups:
        row = [g, str(files_per_group[g])]
        for t in args.terms:
            n, fs = cell.get((g, t), (0, ()))
            row.append(f'{n} in {len(fs)} file{"s" if len(fs) != 1 else ""}' if n else '-')
        rows.append(row)
    widths = [max(len(r[i]) for r in [head] + rows) for i in range(len(head))]
    fmt = lambda r: '  '.join(c.ljust(w) for c, w in zip(r, widths)).rstrip()
    print(fmt(head)); print(fmt(['-' * w for w in widths]))
    for r in rows: print(fmt(r))

    print()
    for t in args.terms:
        found = sorted({g for (g, term) in cell if term == t})
        print(f'{t!r}: ' + (f'found in {len(found)} of {len(groups)} folders ({", ".join(found)})'
                            if found else f'not found in any of {len(groups)} folders'))

    if args.snippets:
        print()
        by_file = {}
        for h in hits:
            by_file.setdefault((h['group'], h['file']), {}).setdefault(h['term'], []).append(h)
        for (g, f), terms in sorted(by_file.items()):
            print(f)
            for t, hs in terms.items():
                print(f'  {t!r}: {len(hs)} hit{"s" if len(hs) != 1 else ""}')
                for h in hs[:args.snippets]:
                    print(f'    [{h["location"]}] {h["snippet"]}')
                if len(hs) > args.snippets:
                    print(f'    ... {len(hs) - args.snippets} more (use --snippets or --csv)')

    if skipped:
        print('\nNot searched (unsupported type): ' + ', '.join(f'{e} x{n}' for e, n in sorted(skipped.items())))
    for rel, err in errors:
        print(f'WARNING could not read {rel}: {err}')

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    p = argparse.ArgumentParser(description="Find words/acronyms across DOCX, XLSX, CSV, TSV and MD files")
    p.add_argument('terms', nargs='+', help='word(s) or acronym(s) to look for')
    p.add_argument('--root', default='.', help='folder that contains the project folders (default: current)')
    p.add_argument('--types', default='docx,xlsx,csv,tsv,md',
                   help='comma-separated file types to search (default: docx,xlsx,csv,tsv,md)')
    p.add_argument('--case', action='store_true', help='case-sensitive')
    p.add_argument('--substring', action='store_true', help='match inside longer words too')
    p.add_argument('--loose', action='store_true', help="allow trailing s / 's")
    p.add_argument('--regex', action='store_true', help='terms are regular expressions')
    p.add_argument('--include-deleted', action='store_true', help='also search tracked-deleted text in DOCX')
    p.add_argument('--snippets', type=int, default=2, help='snippets per term per file (0 = none)')
    p.add_argument('--width', type=int, default=40, help='context characters either side')
    p.add_argument('--csv', help='write every hit to this CSV file')
    args = p.parse_args()

    args.types_set = {t.strip().lower().lstrip('.*') for t in args.types.replace(' ', ',').split(',') if t.strip()}
    unknown = args.types_set - {e.lstrip('.') for e in READERS}
    if unknown:
        print(f'ERROR: unsupported type(s): {", ".join(sorted(unknown))} (choose from docx, xlsx, csv, tsv, md)')
        sys.exit(2)

    if not os.path.isdir(args.root):
        print(f'ERROR: folder not found: {args.root}')
        sys.exit(2)

    hits, files_per_group, skipped, errors = scan(args)
    print_report(args, hits, files_per_group, skipped, errors)

    if args.csv:
        with open(args.csv, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['group', 'file', 'location', 'term', 'snippet'])
            w.writeheader(); w.writerows(hits)
        print(f'\n{len(hits)} hits written to {args.csv}')

    sys.exit(0 if hits else 1)

if __name__ == '__main__':
    main()
