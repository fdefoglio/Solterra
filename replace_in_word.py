"""
replace_in_word_combined.py - ONE command for FAO fixes + smart quotes

Merges:
  - replace_in_word.py  (CSV current->to_replace, longest first, backup)
  - normalize_quotes.py (straight " ' -> curly “ ” ‘ ’ with context)

What it does in one pass per paragraph:
  1. Apply your CSV mapping (e.g. FAO fixes)
  2. Convert straight quotes to smart curly quotes
  3. Save once with single .bak_TIMESTAMP backup

Usage:
  # Both fixes (your case)
  python replace_in_word_combined.py --mapping fao_word_fixes.csv --target Manuscript.docx --normalize-quotes

  # Dry-run first
  python replace_in_word_combined.py --mapping fao_word_fixes.csv --target Manuscript.docx --normalize-quotes --dry-run

  # Only quotes (no CSV)
  python replace_in_word_combined.py --target Manuscript.docx --normalize-quotes

  # Only FAO fixes (no quotes)
  python replace_in_word_combined.py --mapping fao_word_fixes.csv --target Manuscript.docx

  # Whole folder
  python replace_in_word_combined.py --mapping fao_word_fixes.csv --target "P:\path\*.docx" --normalize-quotes

  # Options to disable one type of quote
  python replace_in_word_combined.py --target Doc.docx --normalize-quotes --no-fix-single
"""

import csv, argparse, os, sys, shutil, datetime
from glob import glob

try:
    import docx
    from docx.oxml.ns import qn
    from docx.text.paragraph import Paragraph
except ImportError:
    print("ERROR: python-docx not installed. Run: pip install python-docx")
    sys.exit(1)

# ---------- FAO mapping ----------

def load_mapping(mapping_path):
    mapping = []
    with open(mapping_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if "current" not in reader.fieldnames or "to_replace" not in reader.fieldnames:
            raise ValueError(f"CSV must have headers current,to_replace, got {reader.fieldnames}")
        for row in reader:
            cur = row.get("current","")
            rep = row.get("to_replace","")
            if not cur or cur == rep:
                continue
            mapping.append((cur, rep))
    mapping.sort(key=lambda x: len(x[0]), reverse=True)
    print(f"Loaded {len(mapping)} FAO replacements from {mapping_path}")
    return mapping

# ---------- Smart quotes logic (re-normalizes ALL " and ' quotes) ----------

# Only straight and English curly quotes are touched. « » „ ‚ are left alone
# because they are correct typography in French, Dutch, German, etc.
DOUBLE_QUOTES = {'"', '\u201c', '\u201d'}
SINGLE_QUOTES = {"'", '\u2018', '\u2019'}

# A quote right after one of these (or after whitespace, incl. non-breaking
# space, or at the start) is an opening quote. The curly openers are included
# so nested quotes work: “‘word’ text”
OPENERS = set('([{<') | {'\u2014', '\u2013', '-', '/', '\u201c', '\u2018'}

def is_opening(prev: str, nxt: str) -> bool:
    if prev == '' or prev.isspace() or prev in OPENERS:
        return True
    if prev.isalnum() or nxt == '' or nxt.isspace():
        return False
    # prev is other punctuation (, ; . ! ? ) ...): "a","b" -> opening before a letter
    return nxt.isalnum()

def smarten_text(text: str, fix_double=True, fix_single=True) -> str:
    """Replace quotes 1:1 (the result always has the same length as the input)."""
    if not text or not any(c in text for c in DOUBLE_QUOTES | SINGLE_QUOTES):
        return text

    res = []
    for i, ch in enumerate(text):
        prev = res[-1] if res else ''          # already-converted previous char
        nxt = text[i+1] if i+1 < len(text) else ''

        if ch in DOUBLE_QUOTES and fix_double:
            res.append('\u201c' if is_opening(prev, nxt) else '\u201d')
        elif ch in SINGLE_QUOTES and fix_single:
            if prev == '' and nxt.isdigit():
                res.append('\u2019')           # '90s at paragraph start
            elif is_opening(prev, nxt):
                res.append('\u2018')
            else:
                res.append('\u2019')           # closing quote / apostrophe
        else:
            res.append(ch)
    return ''.join(res)

# ---------- Run-level quote conversion (keeps formatting) ----------

W_P, W_T = qn('w:p'), qn('w:t')
W_BREAKS = {qn('w:tab'): '\t', qn('w:br'): '\n', qn('w:cr'): '\n'}
W_SKIP = {qn('w:pPr'), qn('w:rPr')}

def _text_nodes(el, out):
    """Collect w:t / tab / br elements in document order. Looks inside
    hyperlinks, tracked insertions, smart tags, content controls, etc., but
    not into nested paragraphs (text boxes), which are visited on their own."""
    for child in el:
        tag = child.tag
        if tag == W_P or tag in W_SKIP:
            continue
        if tag == W_T or tag in W_BREAKS:
            out.append(child)
        else:
            _text_nodes(child, out)

def smarten_paragraph(p, fix_double, fix_single) -> bool:
    """Convert quotes in a w:p element in place, run by run. Returns True if changed."""
    nodes = []
    _text_nodes(p, nodes)
    pieces = [(n.text or '') if n.tag == W_T else W_BREAKS[n.tag] for n in nodes]
    text = ''.join(pieces)
    new = smarten_text(text, fix_double, fix_single)
    if new == text:
        return False
    pos = 0
    for n, piece in zip(nodes, pieces):
        if n.tag == W_T and new[pos:pos+len(piece)] != piece:
            n.text = new[pos:pos+len(piece)]
        pos += len(piece)
    return True

# ---------- Paragraph processor (combined) ----------

def process_paragraph(paragraph, mapping, do_quotes, fix_double, fix_single):
    mapping_count = 0

    # 1. FAO replacements (rewrites the paragraph text, as before)
    orig = paragraph.text
    if mapping and orig:
        new_text = orig
        for cur, rep in mapping:
            if cur in new_text:
                mapping_count += new_text.count(cur)
                new_text = new_text.replace(cur, rep)

        if new_text != orig:
            # preserve first run style
            if paragraph.runs:
                first = paragraph.runs[0]
                bold, italic, underline = first.bold, first.italic, first.underline
                fname, fsize = first.font.name, first.font.size
            else:
                bold = italic = underline = fname = fsize = None

            paragraph.text = new_text

            if paragraph.runs:
                r = paragraph.runs[0]
                if bold is not None: r.bold = bold
                if italic is not None: r.italic = italic
                if underline is not None: r.underline = underline
                if fname: r.font.name = fname
                if fsize: r.font.size = fsize
        else:
            mapping_count = 0

    # 2. Smart quotes, applied to the existing runs so formatting survives
    quote_changed = do_quotes and smarten_paragraph(paragraph._p, fix_double, fix_single)

    return mapping_count, (1 if quote_changed else 0)

def process_root(root, parent, *args):
    """Process every paragraph under an XML root: body, tables (nested too),
    text boxes, content controls, headers, footers, footnotes."""
    total_map = total_q = 0
    for p in list(root.iter(W_P)):
        m, q = process_paragraph(Paragraph(p, parent), *args)
        total_map += m
        total_q += q
    return total_map, total_q

NOTE_PARTS = ('/word/footnotes.xml', '/word/endnotes.xml')

def process_docx(path, mapping, do_quotes, fix_double, fix_single, dry_run=False):
    from lxml import etree
    doc = docx.Document(path)
    args = (mapping, do_quotes, fix_double, fix_single)
    total_map = 0
    total_quote_paras = 0

    def add(result):
        nonlocal total_map, total_quote_paras
        total_map += result[0]
        total_quote_paras += result[1]

    # Body (paragraphs, tables, text boxes)
    add(process_root(doc.element.body, doc._body, *args))

    # Headers/Footers (skip ones linked to the previous section; include first-page / even-page)
    for section in doc.sections:
        for hf in (section.header, section.footer,
                   section.first_page_header, section.first_page_footer,
                   section.even_page_header, section.even_page_footer):
            if not hf.is_linked_to_previous:
                add(process_root(hf._element, hf, *args))

    # Footnotes / endnotes (python-docx has no API for them, so edit the XML part)
    for part in doc.part.package.iter_parts():
        if str(part.partname) in NOTE_PARTS:
            root = etree.fromstring(part.blob)
            m, q = process_root(root, None, *args)
            if m or q:
                part._blob = etree.tostring(root, xml_declaration=True,
                                            encoding="UTF-8", standalone=True)
            total_map += m
            total_quote_paras += q

    print(f"{'[DRY] ' if dry_run else ''}{path}: {total_map} FAO, {total_quote_paras} paras with quotes normalized")

    if (total_map or total_quote_paras) and not dry_run:
        backup = str(path) + f".bak_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(path, backup)
        print(f"  Backup -> {backup}")
        doc.save(path)
        print(f"  Saved  -> {path}")

    return total_map, total_quote_paras

def main():
    sys.argv = [a.replace("—","--").replace("–","--") for a in sys.argv]
    p = argparse.ArgumentParser(description="One-pass FAO fixes + smart quotes for .docx")
    p.add_argument("--mapping", help="CSV with current,to_replace (optional if only quotes)")
    p.add_argument("--target", nargs="+", required=True, help=".docx files or *.docx")
    p.add_argument("--normalize-quotes", action="store_true", help="Enable smart quotes conversion")
    p.add_argument("--fix-double", action="store_true", default=True)
    p.add_argument("--no-fix-double", dest="fix_double", action="store_false")
    p.add_argument("--fix-single", action="store_true", default=True)
    p.add_argument("--no-fix-single", dest="fix_single", action="store_false")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    mapping = []
    if args.mapping:
        if not os.path.exists(args.mapping):
            print(f"ERROR: mapping not found: {args.mapping}")
            sys.exit(1)
        mapping = load_mapping(args.mapping)
    else:
        if not args.normalize_quotes:
            print("ERROR: Provide --mapping and/or --normalize-quotes")
            sys.exit(1)

    targets = []
    for pat in args.target:
        pat = pat.strip().strip("\"'")
        expanded = glob(pat)
        if expanded:
            targets.extend(expanded)
        else:
            targets.append(pat)

    tot_map = 0
    tot_quote = 0
    for t in targets:
        if not os.path.exists(t):
            print(f"SKIP not found: {t}")
            continue
        if not t.lower().endswith(".docx"):
            print(f"SKIP not .docx: {t}")
            continue
        m, q = process_docx(t, mapping, args.normalize_quotes, args.fix_double, args.fix_single, args.dry_run)
        tot_map += m
        tot_quote += q

    print(f"\nDONE: {tot_map} FAO replacements, {tot_quote} paragraphs quote-normalized across {len(targets)} file(s)")
    if args.dry_run:
        print("Dry run - no files written")

if __name__ == "__main__":
    main()
