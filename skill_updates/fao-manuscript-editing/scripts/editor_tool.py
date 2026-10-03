"""
README
========

Purpose
-------
Bridge between Microsoft Word documents and Markdown for AI-assisted editing.

v2 changes vs v1
----------------
* Word fields (TOC for List of Tables / Figures), images, hyperlinks,
  bookmarks and content controls are detected on export and tagged
  [SPECIAL]; on import those paragraphs are left completely untouched.
* Footnotes are read from word/footnotes.xml, exported inline as [^fnN],
  and written back on import. You can edit footnote text in the MD.
* Heading styles are preserved. An unchanged heading keeps its original
  style name (e.g. 'heading 10'), instead of being restyled to 'Heading 1'.
* Paragraphs whose text is unchanged are not rebuilt at all, so their
  run-level formatting (colour, font size, kerning) survives byte-for-byte.

Requirements
------------
    pip install python-docx lxml

Usage
-----
    python editor_tool.py --export my_document.docx
    python editor_tool.py --import my_document_for_ai.md my_document.docx

On import the new file is saved as my_document_v1.docx, _v2.docx, ... so
nothing is overwritten.
"""

import os
import re
import sys
import shutil
import zipfile
import tempfile
import argparse
from lxml import etree
from docx import Document


# ---------------------------------------------------------------------------
# Namespace helpers
# ---------------------------------------------------------------------------

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'


def w(tag):
    return '{%s}%s' % (W_NS, tag)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def get_next_version(filename):
    base, ext = os.path.splitext(filename)
    version = 1
    while os.path.exists(f"{base}_v{version}{ext}"):
        version += 1
    return f"{base}_v{version}{ext}"


def detect_heading_level(style_name):
    """
    Handles both 'Heading 1' and your custom 'heading 10'/'heading 20'
    convention, plus Title/Subtitle.
    """
    if not style_name:
        return 0
    s = style_name.strip()
    m = re.search(r'heading\s*(\d+)', s, re.IGNORECASE)
    if m:
        num = int(m.group(1))
        if 10 <= num <= 90 and num % 10 == 0:
            return num // 10
        return min(num, 6)
    if s.lower() == 'title':
        return 1
    if s.lower() == 'subtitle':
        return 2
    return 0


SPECIAL_MARKERS = (
    '<w:fldChar', '<w:instrText', '<w:fldSimple',
    '<w:drawing', '<w:pict', '<w:object',
    '<w:bookmarkStart', '<w:sdt', '<w:hyperlink',
)


def has_unhandled_special_content(para):
    """True if the paragraph contains content we must not rebuild."""
    xml = para._p.xml
    return any(m in xml for m in SPECIAL_MARKERS)


def has_footnote_reference(para):
    return bool(para._p.findall('.//' + w('footnoteReference')))


# ---------------------------------------------------------------------------
# Footnotes (read / write at the OPC level)
# ---------------------------------------------------------------------------

def read_footnotes_xml(docx_path):
    try:
        with zipfile.ZipFile(docx_path) as z:
            data = z.read('word/footnotes.xml')
    except (zipfile.BadZipFile, KeyError):
        return None
    return etree.fromstring(data)


def extract_footnote_texts(fn_root):
    """Return {footnote_id (str): text}."""
    out = {}
    if fn_root is None:
        return out
    for fn in fn_root.findall(w('footnote')):
        fid = fn.get(w('id'))
        if fid in (None, '-1', '0'):      # -1 = separator, 0 = continuationSeparator
            continue
        parts = [t.text or '' for t in fn.findall('.//' + w('t'))]
        out[fid] = ''.join(parts)
    return out


def set_footnote_text(fn_root, fn_id, new_text):
    """Rewrite the body text of one footnote, keeping its formatting."""
    if fn_root is None:
        return
    target = None
    for fn in fn_root.findall(w('footnote')):
        if fn.get(w('id')) == str(fn_id):
            target = fn
            break
    if target is None:
        return

    paras = target.findall(w('p'))
    if not paras:
        p = etree.SubElement(target, w('p'))
        r = etree.SubElement(p, w('r'))
        t = etree.SubElement(r, w('t'))
        t.text = new_text
        return

    p = paras[0]
    runs = p.findall(w('r'))
    # Keep the first run (it carries the footnote reference mark),
    # drop the rest, then replace its text.
    for r in runs[1:]:
        p.remove(r)

    if not runs:
        r = etree.SubElement(p, w('r'))
        t = etree.SubElement(r, w('t'))
        t.text = new_text
        return

    first_r = runs[0]
    for t in first_r.findall(w('t')):
        first_r.remove(t)
    t = etree.SubElement(first_r, w('t'))
    t.text = new_text
    t.set(XML_SPACE, 'preserve')


def write_footnotes_xml(docx_path, fn_root):
    """Replace word/footnotes.xml inside docx_path, rewriting the zip."""
    if fn_root is None:
        return
    new_xml = etree.tostring(
        fn_root, xml_declaration=True, encoding='UTF-8', standalone=True)

    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.docx')
    os.close(tmp_fd)
    try:
        with zipfile.ZipFile(docx_path, 'r') as zin, \
             zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            wrote = False
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == 'word/footnotes.xml':
                    data = new_xml
                    wrote = True
                zout.writestr(item, data)
            if not wrote:
                # python-docx dropped it; add it back. NOTE: if this ever
                # happens, you also need to add the relationship + content
                # type entry. In practice python-docx preserves the part.
                zout.writestr('word/footnotes.xml', new_xml)
        shutil.move(tmp_path, docx_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


# ---------------------------------------------------------------------------
# Markdown tokenisation
# ---------------------------------------------------------------------------

def parse_markdown_segments(text):
    """
    Yield list of (kind, content).
      kind 'text': content = (string, bold, italic, strike)
      kind 'fn':   content = sequence number (int)
    """
    result = []
    i, n = 0, len(text)
    bold = italic = strike = False
    buffer = []

    def flush():
        if buffer:
            result.append(('text', (''.join(buffer), bold, italic, strike)))
            buffer.clear()

    while i < n:
        if text.startswith('***', i):
            flush(); bold = not bold; italic = not italic; i += 3
        elif text.startswith('**', i):
            flush(); bold = not bold; i += 2
        elif text.startswith('~~', i):
            flush(); strike = not strike; i += 2
        elif text.startswith('*', i):
            flush(); italic = not italic; i += 1
        elif text.startswith('[^', i):
            m = re.match(r'\[\^(\d+)\]', text[i:])
            if m:
                flush()
                result.append(('fn', int(m.group(1))))
                i += m.end()
            else:
                buffer.append(text[i]); i += 1
        else:
            buffer.append(text[i]); i += 1
    flush()
    return result


def make_footnote_reference_run(fn_id):
    r = etree.Element(w('r'))
    rPr = etree.SubElement(r, w('rPr'))
    rStyle = etree.SubElement(rPr, w('rStyle'))
    rStyle.set(w('val'), 'FootnoteReference')
    ref = etree.SubElement(r, w('footnoteReference'))
    ref.set(w('id'), str(fn_id))
    return r


# ---------------------------------------------------------------------------
# EXPORT
# ---------------------------------------------------------------------------

def para_to_markdown(para, is_heading, fn_seq_map, fn_seq_counter):
    """Walk <w:p> children in order, producing markdown with [^fnN] markers."""
    pieces = []

    def emit_text(text, rPr):
        if not text:
            return
        bold = italic = strike = False
        if rPr is not None:
            b = rPr.find(w('b'))
            if b is not None and b.get(w('val')) not in ('0', 'false'):
                bold = True
            it = rPr.find(w('i'))
            if it is not None and it.get(w('val')) not in ('0', 'false'):
                italic = True
            s = rPr.find(w('strike'))
            if s is not None and s.get(w('val')) not in ('0', 'false'):
                strike = True
        if bold and not is_heading:
            text = '**' + text + '**'
        if italic:
            text = '*' + text + '*'
        if strike:
            text = '~~' + text + '~~'
        pieces.append(text)

    def walk(el):
        for child in el:
            tag = child.tag
            if tag == w('r'):
                rPr = child.find(w('rPr'))
                for sub in child:
                    if sub.tag == w('t'):
                        emit_text(sub.text or '', rPr)
                    elif sub.tag == w('footnoteReference'):
                        fid = sub.get(w('id'))
                        if fid is None:
                            continue
                        if fid not in fn_seq_map:
                            fn_seq_counter[0] += 1
                            fn_seq_map[fid] = fn_seq_counter[0]
                        pieces.append('[^%d]' % fn_seq_map[fid])
                    elif sub.tag == w('tab'):
                        pieces.append('\t')
                    elif sub.tag == w('br'):
                        pieces.append('\n')
            elif tag in (w('hyperlink'), w('smartTag'), w('sdt'), w('ins')):
                walk(child)

    walk(para._p)
    return ''.join(pieces)


def export_to_labeled_md(docx_path):
    try:
        doc = Document(docx_path)
        base = os.path.splitext(docx_path)[0]
        md_path = f"{base}_for_ai.md"

        # Never silently overwrite an MD that may contain edits
        if os.path.exists(md_path):
            backup = md_path + '.bak'
            shutil.copy(md_path, backup)
            print(f"⚠️  Existing {md_path} backed up to {backup}")

        fn_root = read_footnotes_xml(docx_path)
        fn_texts = extract_footnote_texts(fn_root)

        fn_seq_map = {}
        fn_seq_counter = [0]

        lines = []
        lines.append("<!-- editor_tool v2 export -->")
        lines.append("<!-- Do not change the [N] paragraph numbers. -->")
        lines.append("<!-- Lines tagged [SPECIAL] contain Word fields, images or hyperlinks")
        lines.append("     and will be left untouched on import. -->")
        lines.append("<!-- Footnote references appear inline as [^fnN]; their text is listed at the bottom. -->")
        lines.append("")

        for i, para in enumerate(doc.paragraphs):
            style_name = para.style.name if para.style else ""
            level = detect_heading_level(style_name)
            is_heading = level > 0
            special = has_unhandled_special_content(para)

            body = para_to_markdown(para, is_heading, fn_seq_map, fn_seq_counter)

            tag = "[SPECIAL] " if special else ""
            if is_heading:
                body = "#" * level + " " + body
            if not body.strip():
                body = "[Empty Paragraph]"

            lines.append(f"[{i}] {tag}{body}")
            lines.append("")

        if fn_seq_map:
            lines.append("<!-- FOOTNOTES -->")
            lines.append("<!-- Edit the text after the colon. Do not change the [^fnN]: labels. -->")
            lines.append("")
            seq_to_fid = {seq: fid for fid, seq in fn_seq_map.items()}
            for seq in sorted(seq_to_fid):
                fid = seq_to_fid[seq]
                lines.append(f"[^{seq}]: {fn_texts.get(fid, '')}")
                lines.append("")

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"✅ Export complete: {md_path}")
        print(f"   Paragraphs: {len(doc.paragraphs)}, Footnotes: {len(fn_seq_map)}")
    except Exception:
        import traceback; traceback.print_exc()


# ---------------------------------------------------------------------------
# IMPORT
# ---------------------------------------------------------------------------

def parse_md(md_content):
    """Return (paragraphs: {id:int -> text}, footnotes: {seq:int -> text})."""
    paragraphs, footnotes = {}, {}

    state = None          # 'para' | 'footnote' | None
    current_id = None
    current_lines = []

    def flush():
        nonlocal state, current_id, current_lines
        if state == 'para' and current_id is not None:
            paragraphs[current_id] = '\n'.join(current_lines).rstrip()
        elif state == 'footnote' and current_id is not None:
            footnotes[current_id] = '\n'.join(current_lines).strip()
        state = None
        current_id = None
        current_lines = []

    for line in md_content.split('\n'):
        m_para = re.match(r'^\[(\d+)\]\s?(.*)$', line)
        m_fn   = re.match(r'^\[\^(\d+)\]:\s?(.*)$', line)
        if m_para:
            flush()
            state, current_id = 'para', int(m_para.group(1))
            current_lines = [m_para.group(2)]
        elif m_fn:
            flush()
            state, current_id = 'footnote', int(m_fn.group(1))
            current_lines = [m_fn.group(2)]
        elif line.lstrip().startswith('<!--'):
            flush()
        elif state is not None:
            current_lines.append(line)

    flush()
    return paragraphs, footnotes


def para_plain_and_fns(para):
    """Return (plain_text, [footnote_ids in document order])."""
    plain, fns = [], []

    def walk(el):
        for child in el:
            tag = child.tag
            if tag == w('r'):
                for sub in child:
                    if sub.tag == w('t'):
                        plain.append(sub.text or '')
                    elif sub.tag == w('footnoteReference'):
                        fns.append(sub.get(w('id')))
            elif tag in (w('hyperlink'), w('smartTag'), w('sdt'), w('ins')):
                walk(child)

    walk(para._p)
    return ''.join(plain), fns


def md_plain_and_seqs(text):
    """Return (plain_text, [footnote seq nums]) from markdown."""
    plain, seqs = [], []
    for kind, content in parse_markdown_segments(text):
        if kind == 'text':
            plain.append(content[0])
        elif kind == 'fn':
            seqs.append(content)
    return ''.join(plain), seqs


def apply_markdown_to_para(para, text, fn_seq_map):
    """Rewrite paragraph from markdown. Returns True if it was changed."""
    if has_unhandled_special_content(para):
        return False

    text = text.strip()

    if text == '[Empty Paragraph]' or text == '':
        if para.text.strip() or has_footnote_reference(para):
            for r in list(para._p.findall(w('r'))):
                para._p.remove(r)
            return True
        return False

    # Heading
    heading_match = re.match(r'^(#{1,6})\s+(.*)', text)
    is_heading = False
    if heading_match:
        level = len(heading_match.group(1))
        text = heading_match.group(2)
        is_heading = True
        cur = detect_heading_level(para.style.name if para.style else "")
        if cur != level:
            try:
                para.style = f'Heading {level}'
            except Exception:
                pass

    # No-op if nothing actually changed
    old_plain, old_fns = para_plain_and_fns(para)
    new_plain, new_seqs = md_plain_and_seqs(text)
    if old_plain == new_plain and len(old_fns) == len(new_seqs):
        return False

    # Rebuild runs (safe — has_unhandled_special_content already returned False)
    for r in list(para._p.findall(w('r'))):
        para._p.remove(r)

    for kind, content in parse_markdown_segments(text):
        if kind == 'text':
            string, bold, italic, strike = content
            if not string:
                continue
            run = para.add_run(string)
            if bold and not is_heading:
                run.bold = True
            if italic:
                run.italic = True
            if strike:
                run.font.strike = True
        elif kind == 'fn':
            fid = fn_seq_map.get(content)
            if fid is None:
                continue
            para._p.append(make_footnote_reference_run(fid))
    return True


def import_ai_edits(docx_path, response_path):
    try:
        doc = Document(docx_path)

        with open(response_path, 'r', encoding='utf-8') as f:
            content = f.read()

        paragraphs, footnotes = parse_md(content)

        # Reproduce the sequence->id mapping the exporter used
        fn_root = read_footnotes_xml(docx_path)
        fn_seq_map = {}
        fn_seq_counter = [0]
        for para in doc.paragraphs:
            is_heading = detect_heading_level(
                para.style.name if para.style else "") > 0
            para_to_markdown(para, is_heading, fn_seq_map, fn_seq_counter)

        print(f"🔄 Applying {len(paragraphs)} paragraph edits "
              f"and {len(footnotes)} footnote edits …")

        changed = 0
        for pid, text in paragraphs.items():
            if text.lstrip().startswith('[SPECIAL]'):
                continue
            if pid < len(doc.paragraphs):
                if apply_markdown_to_para(doc.paragraphs[pid], text, fn_seq_map):
                    changed += 1
            else:
                print(f"⚠️  ID [{pid}] exceeds document length.")

        # Apply footnote edits to XML tree
        if fn_root is not None and footnotes:
            seq_to_fid = {seq: fid for fid, seq in fn_seq_map.items()}
            for seq, new_text in footnotes.items():
                fid = seq_to_fid.get(seq)
                if fid is not None:
                    set_footnote_text(fn_root, fid, new_text)

        output_path = get_next_version(docx_path)
        doc.save(output_path)

        # Re-patch footnotes.xml into the saved package
        if fn_root is not None:
            write_footnotes_xml(output_path, fn_root)

        print(f"✅ Import complete: {output_path}")
        print(f"   Paragraphs changed: {changed}")

    except Exception:
        import traceback; traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        description='AI Language Editor: Word <-> Markdown bridge (v2)')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--export', action='store_true',
                       help='Export DOCX to labeled Markdown')
    group.add_argument('--import', dest='import_file', metavar='RESPONSE',
                       help='Import AI-edited Markdown back into a new DOCX')
    parser.add_argument('docx', help='Source Word document (.docx)')

    args = parser.parse_args()
    if args.export:
        export_to_labeled_md(args.docx)
    elif args.import_file:
        import_ai_edits(args.docx, args.import_file)


if __name__ == '__main__':
    main()