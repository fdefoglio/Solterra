"""
README
========

Purpose
-------
Bridge between Microsoft Word documents and Markdown for AI-assisted editing.

v3 changes vs v2
----------------
* Far fewer [SPECIAL] paragraphs. Bookmarks (Word puts _Toc/_Hlk/_Ref
  bookmarks on most headings), hyperlinks, tracked changes and comment ranges
  no longer freeze a paragraph: its text is editable and those elements are
  kept in place on import. Hyperlink text (e.g. URLs in reference entries)
  is editable; if a link whose text was its own URL gets a new URL, the link
  target is updated as well.
* Fields (cross-references, Zotero/EndNote/Mendeley citations, SEQ numbers,
  page numbers), images, equations, content controls, symbols and page breaks
  appear inline as protected tokens, for example
      As shown in ⟦3|Table 3⟧, tenure ... ⟦4|(FAO, 2012)⟧.
  A token must stay in its paragraph exactly once (it may move within the
  paragraph). The text after | is for reading only: Word regenerates it, so
  edits inside a token are ignored. If a token is lost or duplicated, that
  paragraph is left unchanged and listed in the import report.
* Changed paragraphs are patched against the original text instead of being
  rebuilt, so unchanged words keep their run formatting (font, size, colour,
  superscript/subscript, highlighting). Bold/italic/strikethrough come from
  the Markdown as before.
* [SPECIAL] is now only used for paragraphs that belong to a field spanning
  several paragraphs (Table of Contents, List of Tables/Figures) and for
  multi-paragraph footnotes. Those are still left untouched on import.
* Footnotes: unchanged footnotes are no longer rewritten; edited footnotes keep
  their formatting and links (v2 moved the text into the superscript
  reference-mark run and duplicated hyperlink text).
* Markdown exported by v2 can still be imported.

v2 features (unchanged)
-----------------------
* Footnotes are exported inline as [^N] and written back on import.
* Heading styles are preserved (an unchanged heading keeps e.g. 'heading 10').
* Paragraphs whose text is unchanged are not touched at all.

Requirements
------------
    pip install python-docx lxml

Usage
-----
    python editor_tool.py --export my_document.docx
    python editor_tool.py --import my_document_for_ai.md my_document.docx

    # Review copy of a finished DOCX: same labels and tokens, plus page numbers,
    # tables and a figure/table inventory as read-only comments. Lets a review
    # run on the Markdown alone instead of on the attached DOCX.
    python editor_tool.py --export --review my_document.docx   # -> my_document_for_review.md

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
from collections import Counter
from difflib import SequenceMatcher
from lxml import etree
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement, parse_xml
from docx.text.run import Run


# ---------------------------------------------------------------------------
# Namespace helpers
# ---------------------------------------------------------------------------

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
A_GRAPHIC_DATA = '{http://schemas.openxmlformats.org/drawingml/2006/main}graphicData'
WP_DOCPR = '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr'
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'


def w(tag):
    return '{%s}%s' % (W_NS, tag)


W_P, W_R, W_T, W_RPR, W_PPR = w('p'), w('r'), w('t'), w('rPr'), w('pPr')
R_ID = '{%s}id' % R_NS

EXPORT_HEADER_V3 = '<!-- editor_tool v3 export -->'

TOK_OPEN, TOK_CLOSE = '⟦', '⟧'          # ⟦ ⟧
TOKEN_RE = re.compile('⟦(\\d+)(?:\\|[^⟧\\n]*)?⟧')


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


def _local(el):
    return etree.QName(el).localname if isinstance(el.tag, str) else ''


def _on(rPr, tag):
    if rPr is None:
        return False
    el = rPr.find(w(tag))
    return el is not None and el.get(w('val')) not in ('0', 'false', 'off')


def run_fmt(run):
    """(bold, italic, strike) from a run's direct formatting."""
    rPr = run.find(W_RPR) if run is not None else None
    return (_on(rPr, 'b'), _on(rPr, 'i'), _on(rPr, 'strike'))


# ---------------------------------------------------------------------------
# Footnotes (read / write at the OPC level)
# ---------------------------------------------------------------------------

def read_footnotes_xml(docx_path):
    try:
        with zipfile.ZipFile(docx_path) as z:
            data = z.read('word/footnotes.xml')
    except (zipfile.BadZipFile, KeyError):
        return None
    return parse_xml(data)


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


def find_footnote(fn_root, fid):
    if fn_root is None:
        return None
    for fn in fn_root.findall(w('footnote')):
        if fn.get(w('id')) == str(fid):
            return fn
    return None


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
      kind 'tok':  content = protected token number (int)
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
        if text.startswith(TOK_OPEN, i) and TOKEN_RE.match(text, i):
            m = TOKEN_RE.match(text, i)
            flush()
            result.append(('tok', int(m.group(1))))
            i = m.end()
        elif text.startswith('***', i):
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
    r = OxmlElement('w:r')
    rPr = etree.SubElement(r, w('rPr'))
    rStyle = etree.SubElement(rPr, w('rStyle'))
    rStyle.set(w('val'), 'FootnoteReference')
    ref = etree.SubElement(r, w('footnoteReference'))
    ref.set(w('id'), str(fn_id))
    return r


# ---------------------------------------------------------------------------
# Paragraph model: the paragraph as a stream of characters, footnote
# references and protected tokens, plus zero-width markers (bookmarks, ...)
# ---------------------------------------------------------------------------

# Wrappers whose text stays editable; they are re-created around the new text.
CONTAINER_TAGS = {w('hyperlink'), w('ins'), w('moveTo'), w('smartTag'),
                  w('customXml'), w('dir'), w('bdo')}
# Zero-width elements: kept, re-anchored to the nearest surviving character.
MARKER_TAGS = {w(t) for t in (
    'bookmarkStart', 'bookmarkEnd', 'commentRangeStart', 'commentRangeEnd',
    'permStart', 'permEnd', 'del', 'moveFrom',
    'moveFromRangeStart', 'moveFromRangeEnd', 'moveToRangeStart', 'moveToRangeEnd',
    'customXmlInsRangeStart', 'customXmlInsRangeEnd',
    'customXmlDelRangeStart', 'customXmlDelRangeEnd')}
# Spell/grammar marks; Word regenerates them, so they are dropped on rebuild.
DROP_TAGS = {w('proofErr')}
SIMPLE_RUN_CHILDREN = {w(t) for t in (
    'rPr', 't', 'tab', 'br', 'cr', 'noBreakHyphen', 'softHyphen',
    'lastRenderedPageBreak', 'footnoteReference')}
REF_MARK_TAGS = {w('footnoteRef'), w('endnoteRef')}


class CharItem:
    __slots__ = ('sym', 'run', 'chain', 'src', 'fmt')

    def __init__(self, sym, run, chain, src, fmt):
        self.sym, self.run, self.chain, self.src, self.fmt = sym, run, chain, src, fmt


class FnItem:
    __slots__ = ('sym', 'run', 'chain', 'ref')

    def __init__(self, seq, run, chain, ref):
        self.sym, self.run, self.chain, self.ref = ('F', seq), run, chain, ref


class TokItem:
    __slots__ = ('sym', 'elems', 'label', 'chain')

    def __init__(self, num, elems, label):
        self.sym, self.elems, self.label, self.chain = ('T', num), elems, label, ()


class ParaModel:
    def __init__(self, p):
        self.p = p
        self.items = []
        self.markers = []         # (position in items, element, chain)


class Ctx:
    """Numbering shared by export and import, so both see the same IDs."""

    def __init__(self):
        self.next_token = 0
        self.fn_seq_map = {}      # footnote id (str) -> sequence number
        self.fn_seq_counter = [0]

    def token_num(self):
        self.next_token += 1
        return self.next_token

    def fn_seq(self, fid):
        if fid not in self.fn_seq_map:
            self.fn_seq_counter[0] += 1
            self.fn_seq_map[fid] = self.fn_seq_counter[0]
        return self.fn_seq_map[fid]


def _fld_counts(el):
    begins = ends = 0
    for fc in el.iter(w('fldChar')):
        t = fc.get(w('fldCharType'))
        if t == 'begin':
            begins += 1
        elif t == 'end':
            ends += 1
    return begins, ends


def _run_is_simple(r):
    for c in r:
        if not isinstance(c.tag, str):
            continue
        if c.tag not in SIMPLE_RUN_CHILDREN:
            return False
        if c.tag == w('br') and c.get(w('type')) not in (None, 'textWrapping'):
            return False
    return True


def _is_ref_mark_run(r):
    kids = [c for c in r if isinstance(c.tag, str) and c.tag != W_RPR]
    return bool(kids) and all(c.tag in REF_MARK_TAGS for c in kids)


def _is_props(el):
    return _local(el).endswith('Pr')


def _container_is_simple(el):
    for c in el:
        if not isinstance(c.tag, str) or _is_props(c):
            continue
        if c.tag == W_R:
            if not _run_is_simple(c):
                return False
        elif c.tag in CONTAINER_TAGS:
            if not _container_is_simple(c):
                return False
        elif c.tag not in MARKER_TAGS and c.tag not in DROP_TAGS:
            return False
    return True


def _clean_label(s, limit=60):
    s = re.sub(r'\s+', ' ', s.replace(TOK_OPEN, ' ').replace(TOK_CLOSE, ' ')).strip()
    return s if len(s) <= limit else s[:limit - 1].rstrip() + '…'


def token_label(elems):
    text = ''.join(t.text or '' for e in elems for t in e.iter(W_T))
    tags = {x.tag for e in elems for x in e.iter() if isinstance(x.tag, str)}
    if tags & {w('drawing'), w('pict'), w('object')}:
        uris = ' '.join(g.get('uri', '') for e in elems for g in e.iter(A_GRAPHIC_DATA))
        if 'chart' in uris:
            kind = 'chart'
        elif 'diagram' in uris:
            kind = 'diagram'
        elif w('txbxContent') in tags:
            kind = 'text box'
        elif 'wordprocessingShape' in uris or 'wordprocessingGroup' in uris:
            kind = 'shape'
        elif w('object') in tags:
            kind = 'embedded object'
        else:
            kind = 'image'
        alt = next((d.get('descr') or d.get('title') for e in elems for d in e.iter(WP_DOCPR)
                    if d.get('descr') or d.get('title')), '')
        detail = text.strip() or alt
        return _clean_label(kind + (': ' + detail if detail else ''))
    if tags & {'{%s}oMath' % M_NS, '{%s}oMathPara' % M_NS}:
        return 'equation'
    if text.strip():
        return _clean_label(text)
    instr = ''.join(x.text or '' for e in elems for x in e.iter(w('instrText')))
    instr = instr or (elems[0].get(w('instr')) or '')
    if instr.strip():
        return _clean_label(instr.split()[0] + ' field')
    for e in elems:
        for br in e.iter(w('br')):
            if br.get(w('type')):
                return br.get(w('type')) + ' break'
    if w('sym') in tags:
        return 'symbol'
    if w('endnoteReference') in tags:
        return 'endnote'
    return _local(elems[0]) or 'object'


def scan_paragraph(p, ctx, legacy=False, depth_in=0):
    """
    Build the ParaModel of a <w:p>. Returns (model, depth_out); model is None
    when the paragraph is part of a field that spans several paragraphs
    (TOC, List of Tables/Figures) and must be left untouched.
    legacy=True reproduces what a v2 export showed (non-breaking hyphens
    were not exported), so v2 Markdown can be imported.
    """
    b, e = _fld_counts(p)
    depth_out = max(depth_in + b - e, 0)
    if depth_in > 0 or depth_out > 0:
        return None, depth_out

    model = ParaModel(p)

    def add_token(elems):
        model.items.append(TokItem(ctx.token_num(), elems, token_label(elems)))

    def classify(el, chain):
        tag = el.tag
        if not isinstance(tag, str):
            return
        if tag == W_R:
            if _is_ref_mark_run(el):
                model.markers.append((len(model.items), el, chain))
            elif _run_is_simple(el):
                fmt = run_fmt(el)
                for c in el:
                    ct = c.tag
                    if ct == W_T:
                        for ch in (c.text or ''):
                            model.items.append(CharItem(ch, el, chain, None, fmt))
                    elif ct == w('tab'):
                        model.items.append(CharItem('\t', el, chain, c, fmt))
                    elif ct in (w('br'), w('cr')):
                        model.items.append(CharItem('\n', el, chain, c, fmt))
                    elif ct == w('noBreakHyphen'):
                        if legacy:
                            m = OxmlElement('w:r')
                            if el.find(W_RPR) is not None:
                                m.append(parse_xml(etree.tostring(el.find(W_RPR))))
                            m.append(OxmlElement('w:noBreakHyphen'))
                            model.markers.append((len(model.items), m, chain))
                        else:
                            model.items.append(CharItem('\u2011', el, chain, c, fmt))
                    elif ct == w('footnoteReference'):
                        fid = c.get(w('id'))
                        if fid is not None:
                            model.items.append(FnItem(ctx.fn_seq(fid), el, chain, c))
            else:
                add_token([el])
        elif tag in CONTAINER_TAGS:
            if _container_is_simple(el):
                for c in el:
                    if isinstance(c.tag, str) and not _is_props(c):
                        classify(c, chain + (el,))
            else:
                add_token([el])
        elif tag in MARKER_TAGS:
            model.markers.append((len(model.items), el, chain))
        elif tag in DROP_TAGS:
            pass
        else:
            add_token([el])

    depth, unit = 0, None
    for child in p:
        if not isinstance(child.tag, str) or child.tag == W_PPR:
            continue
        cb, ce = _fld_counts(child)
        if depth > 0 or cb > 0:
            # a complex field: everything from 'begin' to 'end' is one token
            if unit is None:
                unit = []
            unit.append(child)
            depth += cb - ce
            if depth <= 0:
                add_token(unit)
                depth, unit = 0, None
            continue
        classify(child, ())
    if unit:
        return None, depth_out
    return model, depth_out


def model_to_md(model, is_heading):
    out, buf = [], []
    cur = None

    def flush():
        if buf:
            text = ''.join(buf)
            bold, italic, strike = cur
            if bold and not is_heading:
                text = '**' + text + '**'
            if italic:
                text = '*' + text + '*'
            if strike:
                text = '~~' + text + '~~'
            out.append(text)
            buf.clear()

    for it in model.items:
        if isinstance(it, CharItem):
            fmt = it.fmt
            if fmt != cur:
                flush()
                cur = fmt
            buf.append(it.sym)
        else:
            flush()
            if isinstance(it, FnItem):
                out.append('[^%d]' % it.sym[1])
            else:
                out.append('%s%d|%s%s' % (TOK_OPEN, it.sym[1], it.label, TOK_CLOSE))
    flush()
    return ''.join(out)


def model_plain(model):
    return ''.join(it.sym for it in model.items if isinstance(it, CharItem))


# ---------------------------------------------------------------------------
# Applying edited text to a paragraph model
# ---------------------------------------------------------------------------

def md_to_stream(text, plain=False):
    """[(sym, fmt)] where fmt = (bold, italic, strike), or None = inherit."""
    if plain:
        return [(ch, None) for ch in text]
    out = []
    for kind, content in parse_markdown_segments(text):
        if kind == 'text':
            s, b, i, st = content
            out.extend((ch, (b, i, st)) for ch in s)
        elif kind == 'fn':
            out.append((('F', content), None))
        elif kind == 'tok':
            out.append((('T', content), None))
    return out


def _groups(syms):
    """Split into words / whitespace runs / single other symbols, for diffing."""
    groups, cur, cls = [], [], None
    for s in syms:
        if isinstance(s, str) and (s.isalnum() or s == '_'):
            c = 'w'
        elif isinstance(s, str) and s.isspace():
            c = 's'
        else:
            c = None
        if c is not None and c == cls:
            cur.append(s)
        else:
            if cur:
                groups.append(tuple(cur))
            cur, cls = [s], c
    if cur:
        groups.append(tuple(cur))
    return groups


def align(old_syms, new_syms):
    """src[j] = index of the old symbol that new symbol j is kept from, or None."""
    src = [None] * len(new_syms)
    og, ng = _groups(old_syms), _groups(new_syms)
    ostart, nstart = [0], [0]
    for g in og:
        ostart.append(ostart[-1] + len(g))
    for g in ng:
        nstart.append(nstart[-1] + len(g))
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, og, ng, autojunk=False).get_opcodes():
        a0, a1, b0, b1 = ostart[i1], ostart[i2], nstart[j1], nstart[j2]
        if tag == 'equal':
            for k in range(b1 - b0):
                src[b0 + k] = a0 + k
        elif tag == 'replace':
            sm = SequenceMatcher(None, old_syms[a0:a1], new_syms[b0:b1], autojunk=False)
            for t2, x1, x2, y1, y2 in sm.get_opcodes():
                if t2 == 'equal':
                    for k in range(x2 - x1):
                        src[b0 + y1 + k] = a0 + x1 + k
    return src


def _common_prefix(a, b):
    out = []
    for x, y in zip(a, b):
        if x is not y:
            break
        out.append(x)
    return tuple(out)


def _clone_container(c):
    clone = c.makeelement(c.tag, dict(c.attrib))
    for sub in c:
        if isinstance(sub.tag, str) and _is_props(sub):
            clone.append(parse_xml(etree.tostring(sub)))
    return clone


def _make_run(base_run, fmt, ignore_bold):
    r = OxmlElement('w:r')
    base_rPr = base_run.find(W_RPR) if base_run is not None else None
    if base_rPr is not None:
        r.append(parse_xml(etree.tostring(base_rPr)))
    if fmt is not None:
        bb, bi, bs = run_fmt(base_run)
        tb, ti, ts = fmt
        run = Run(r, None)
        if not ignore_bold and tb != bb:
            run.bold = True if tb else None
        if ti != bi:
            run.italic = True if ti else None
        if ts != bs:
            run.font.strike = True if ts else None
    return r


URL_RE = re.compile(r'^(https?://|www\.|doi\.org/)\S+$', re.IGNORECASE)


def _norm_url(s):
    return re.sub(r'^https?://', '', s.strip(), flags=re.IGNORECASE).rstrip('/').lower()


def apply_text(p, model, text, ctx, ignore_bold=False, plain=False, part=None, notes=None):
    """
    Patch <w:p> p so that it reads `text` (Markdown, or plain text when
    plain=True). Returns (changed: bool, error: str or None).
    """
    notes = notes if notes is not None else []
    old = model.items
    new = md_to_stream(text, plain)

    # Markdown cannot carry leading/trailing whitespace: keep the original's.
    lead = 0
    while lead < len(old) and isinstance(old[lead], CharItem) and old[lead].sym.isspace():
        lead += 1
    trail = 0
    while trail < len(old) - lead and isinstance(old[-1 - trail], CharItem) and old[-1 - trail].sym.isspace():
        trail += 1
    new = [(it.sym, None) for it in old[:lead]] + new + \
          [(it.sym, None) for it in old[len(old) - trail:]]

    # Protected tokens must all be present exactly once.
    old_toks = Counter(it.sym[1] for it in old if isinstance(it, TokItem))
    new_toks = Counter(s[1] for s, _ in new if isinstance(s, tuple) and s[0] == 'T')
    if old_toks != new_toks:
        missing = sorted((old_toks - new_toks).elements())
        extra = sorted((new_toks - old_toks).elements())
        parts = []
        if missing:
            parts.append('token(s) %s missing' % ', '.join('⟦%d⟧' % n for n in missing))
        if extra:
            parts.append('token(s) %s duplicated or not from this paragraph'
                         % ', '.join('⟦%d⟧' % n for n in extra))
        return False, '; '.join(parts)

    # Unknown footnote numbers are dropped (as in v2).
    seq_to_fid = {seq: fid for fid, seq in ctx.fn_seq_map.items()}
    for s, _ in new:
        if isinstance(s, tuple) and s[0] == 'F' and s[1] not in seq_to_fid:
            notes.append('footnote [^%d] does not exist and was dropped' % s[1])
    new = [(s, f) for s, f in new
           if not (isinstance(s, tuple) and s[0] == 'F' and s[1] not in seq_to_fid)]

    old_syms = [it.sym for it in old]
    new_syms = [s for s, _ in new]

    def old_fmt(it):
        f = it.fmt
        return (False,) + f[1:] if ignore_bold else f

    def new_fmt(j, it):
        f = new[j][1]
        if f is None:
            return old_fmt(it) if it is not None else None
        return (False,) + f[1:] if ignore_bold else f

    # Nothing changed?
    if old_syms == new_syms and all(
            not isinstance(old[j], CharItem) or new_fmt(j, old[j]) == old_fmt(old[j])
            for j in range(len(old))):
        return False, None

    src = align(old_syms, new_syms)

    def chain_of(i):
        return old[i].chain if i is not None else ()

    prev_src, last = [], None
    for j in range(len(new)):
        prev_src.append(last)
        if src[j] is not None:
            last = src[j]
    next_src, nxt = [None] * len(new), None
    for j in range(len(new) - 1, -1, -1):
        next_src[j] = nxt
        if src[j] is not None:
            nxt = src[j]

    base_cache = {}

    # Text glued onto the end of a link/wrapper without a space (e.g. a URL
    # that got longer) extends it; trailing punctuation does not.
    extend = {}
    j = 0
    while j < len(new):
        if src[j] is not None:
            j += 1
            continue
        k = j
        while k < len(new) and src[k] is None:
            k += 1
        pi = prev_src[j]
        if pi is not None and isinstance(old[pi], CharItem) and not old[pi].sym.isspace() \
                and len(chain_of(pi)) > len(_common_prefix(chain_of(pi), chain_of(next_src[j]))):
            n = 0
            while j + n < k and isinstance(new[j + n][0], str) and not new[j + n][0].isspace():
                n += 1
            while n and new[j + n - 1][0] in '.,;:!?)]}\'"\u2019\u201d':
                n -= 1
            for x in range(j, j + n):
                extend[x] = (old[pi].chain, old[pi].run)
        j = k

    def inherited(j):
        """(chain, base run) for an inserted symbol."""
        if j in extend:
            return extend[j]
        key = (prev_src[j], next_src[j])
        if key not in base_cache:
            pi, qi = key
            chain = _common_prefix(chain_of(pi), chain_of(qi))
            base = None
            order = (list(range(pi, -1, -1)) if pi is not None else []) + \
                    (list(range(qi, len(old))) if qi is not None else [])
            for k in order:
                it = old[k]
                if isinstance(it, CharItem) and len(it.chain) == len(chain) and \
                        all(a is b for a, b in zip(it.chain, chain)):
                    base = it.run
                    break
            base_cache[key] = (chain, base)
        return base_cache[key]

    # Markers go before the first surviving old symbol at/after their position.
    old_to_new = {}
    for j, i in enumerate(src):
        if i is not None:
            old_to_new[i] = j
    first_alive = [len(new)] * (len(old) + 1)
    for i in range(len(old) - 1, -1, -1):
        first_alive[i] = old_to_new.get(i, first_alive[i + 1])
    markers_at = {}
    for pos, el, chain in model.markers:
        markers_at.setdefault(first_alive[pos], []).append((el, chain))

    tok_by_num = {it.sym[1]: it for it in old if isinstance(it, TokItem)}

    # ---- rebuild ----
    for c in list(p):
        if c.tag != W_PPR:
            p.remove(c)

    stack = []              # [(original container, clone)]
    clones = []             # all hyperlink clones, for link retargeting

    def target(chain):
        k = 0
        while k < len(stack) and k < len(chain) and stack[k][0] is chain[k]:
            k += 1
        del stack[k:]
        for c in chain[k:]:
            clone = _clone_container(c)
            (stack[-1][1] if stack else p).append(clone)
            stack.append((c, clone))
            if c.tag == w('hyperlink'):
                clones.append((c, clone))
        return stack[-1][1] if stack else p

    cur = {'key': None, 'r': None, 'buf': []}

    def flush_text():
        if cur['buf']:
            t = etree.SubElement(cur['r'], W_T)
            t.text = ''.join(cur['buf'])
            t.set(XML_SPACE, 'preserve')
            cur['buf'] = []

    def close_run():
        flush_text()
        cur['key'] = cur['r'] = None

    def emit_markers(j):
        for el, chain in markers_at.get(j, ()):
            close_run()
            target(chain).append(el)

    for j, (sym, _) in enumerate(new):
        emit_markers(j)
        i = src[j]
        it = old[i] if i is not None else None
        if isinstance(sym, tuple) and sym[0] == 'T':
            close_run()
            target(())
            for el in tok_by_num[sym[1]].elems:
                p.append(el)
        elif isinstance(sym, tuple) and sym[0] == 'F':
            close_run()
            if it is not None:
                r = OxmlElement('w:r')
                if it.run.find(W_RPR) is not None:
                    r.append(parse_xml(etree.tostring(it.run.find(W_RPR))))
                r.append(parse_xml(etree.tostring(it.ref)))
                target(it.chain).append(r)
            else:
                chain, _ = inherited(j)
                target(chain).append(make_footnote_reference_run(seq_to_fid[sym[1]]))
        else:
            if it is not None:
                chain, base, srcel = it.chain, it.run, it.src
            else:
                (chain, base), srcel = inherited(j), None
            fmt = new_fmt(j, it if it is not None else None)
            if fmt is None and base is not None:
                fmt = run_fmt(base)
            new_r = None
            key = (tuple(id(c) for c in chain), id(base), fmt)
            if key != cur['key']:
                # merge with the previous run when the formatting is identical
                new_r = _make_run(base, fmt, ignore_bold)
                rpr = new_r.find(W_RPR)
                key = (key[0], etree.tostring(rpr) if rpr is not None else b'')
            if key != cur['key']:
                close_run()
                cur['r'] = new_r
                target(chain).append(cur['r'])
                cur['key'] = key
            if sym in ('\t', '\n', '\u2011'):
                flush_text()
                if srcel is not None:
                    cur['r'].append(parse_xml(etree.tostring(srcel)))
                else:
                    cur['r'].append(OxmlElement(
                        {'\t': 'w:tab', '\n': 'w:br', '\u2011': 'w:noBreakHyphen'}[sym]))
            else:
                cur['buf'].append(sym)
    emit_markers(len(new))
    close_run()

    # A link whose text was its own URL follows a URL change in the text.
    by_orig = {}
    for orig, clone in clones:
        by_orig.setdefault(id(orig), (orig, []))[1].append(clone)
    for orig, cl in by_orig.values():
        rid = orig.get(R_ID)
        if not rid:
            continue
        old_text = ''.join(t.text or '' for t in orig.iter(W_T))
        new_text = ''.join(t.text or '' for c in cl for t in c.iter(W_T)).strip()
        if old_text.strip() == new_text or not URL_RE.match(new_text) or not URL_RE.match(old_text.strip()):
            continue
        if part is None:
            notes.append('link text changed to %s but the link target could not be updated' % new_text)
            continue
        rel = part.rels.get(rid)
        if rel is None or not rel.is_external or _norm_url(rel.target_ref) != _norm_url(old_text):
            continue
        new_url = new_text if re.match(r'^https?://', new_text, re.I) else 'https://' + new_text
        new_rid = part.relate_to(new_url, RT.HYPERLINK, is_external=True)
        for c in cl:
            c.set(R_ID, new_rid)
        notes.append('link target updated to %s' % new_url)

    return True, None


# ---------------------------------------------------------------------------
# Whole-document scanning (identical for export and import)
# ---------------------------------------------------------------------------

def legacy_para_to_markdown(para, is_heading, fn_seq_map, fn_seq_counter):
    """v2 exporter: used for [SPECIAL] paragraphs and footnote numbering."""
    pieces = []

    def emit_text(text, rPr):
        if not text:
            return
        bold = italic = strike = False
        if rPr is not None:
            bold, italic, strike = _on(rPr, 'b'), _on(rPr, 'i'), _on(rPr, 'strike')
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


def heading_levels(paras):
    """Heading level per paragraph (0 = not a heading); style lookups are slow."""
    cache, out = {}, []
    for para in paras:
        sid = para._p.style
        if sid not in cache:
            cache[sid] = detect_heading_level(para.style.name if para.style else "")
        out.append(cache[sid])
    return out


def scan_document(doc, fn_root, legacy=False):
    """Return (ctx, paragraphs, heading levels, [body models or None],
    {seq: footnote model or None})."""
    ctx = Ctx()
    paras = doc.paragraphs
    levels = heading_levels(paras)
    # Footnote numbering exactly as v2 assigned it
    for para, level in zip(paras, levels):
        legacy_para_to_markdown(para, level > 0, ctx.fn_seq_map, ctx.fn_seq_counter)

    models, depth = [], 0
    for para in paras:
        model, depth = scan_paragraph(para._p, ctx, legacy, depth)
        models.append(model)

    fn_models = {}
    for fid, seq in sorted(ctx.fn_seq_map.items(), key=lambda x: x[1]):
        fn = find_footnote(fn_root, fid)
        fn_paras = fn.findall(W_P) if fn is not None else []
        if len(fn_paras) == 1:
            fn_models[seq], _ = scan_paragraph(fn_paras[0], ctx, legacy)
        else:
            fn_models[seq] = None
    return ctx, paras, levels, models, fn_models


# ---------------------------------------------------------------------------
# Review export: page numbers, tables, figures (read-only context)
# ---------------------------------------------------------------------------

OBJECT_KINDS = ('image', 'chart', 'diagram', 'text box', 'shape', 'embedded object')


def page_layout(doc):
    """
    Pages as Word last laid the document out, from its w:lastRenderedPageBreak
    markers. Returns (page of each body paragraph or None when the file holds
    no page information, [(index of the paragraph before, page, <w:tbl>)]).
    A paragraph's page is where its first text starts.
    """
    lrpb = w('lastRenderedPageBreak')
    page, para_pages, tables, found, pi = 1, [], [], False, -1
    for child in doc.element.body:
        if child.tag not in (W_P, w('tbl')):
            page += sum(1 for _ in child.iter(lrpb))
            continue
        before, total, seen_text = 0, 0, False
        for el in child.iter(lrpb, W_T):
            if el.tag == lrpb:
                total += 1
                if not seen_text:
                    before += 1
            elif (el.text or '').strip():
                seen_text = True
        found = found or total > 0
        if child.tag == W_P:
            pi += 1
            para_pages.append(page + before)
        else:
            tables.append((pi, page + before, child))
        page += total
    return (para_pages if found else None), tables


def _cell_text(el, escape=True):
    paras = [''.join(t.text or '' for t in p.iter(W_T)).strip() for p in el.iter(W_P)]
    text = ' / '.join(p for p in paras if p).replace('-->', '\u2014>').replace('\n', ' ')
    return text.replace('|', '\\|') if escape else text


def table_to_md(tbl):
    rows = []
    for tr in tbl.findall(w('tr')):
        cells = []
        for tc in tr.findall(w('tc')):
            cells.append(_cell_text(tc))
            span = tc.find(w('tcPr') + '/' + w('gridSpan'))
            if span is not None and (span.get(w('val')) or '1').isdigit():
                cells.extend([''] * (int(span.get(w('val'))) - 1))
        rows.append(cells)
    if not rows:
        return []
    width = max(len(r) for r in rows) or 1
    rows = [r + [''] * (width - len(r)) for r in rows]
    out = ['| ' + ' | '.join(rows[0]) + ' |', '|' + ' --- |' * width]
    out += ['| ' + ' | '.join(r) + ' |' for r in rows[1:]]
    return out


# ---------------------------------------------------------------------------
# EXPORT
# ---------------------------------------------------------------------------

def export_to_labeled_md(docx_path, review=False):
    try:
        doc = Document(docx_path)
        base = os.path.splitext(docx_path)[0]
        md_path = f"{base}_for_review.md" if review else f"{base}_for_ai.md"

        # Never silently overwrite an MD that may contain edits
        if os.path.exists(md_path):
            backup = md_path + '.bak'
            shutil.copy(md_path, backup)
            print(f"⚠️  Existing {md_path} backed up to {backup}")

        fn_root = read_footnotes_xml(docx_path)
        fn_texts = extract_footnote_texts(fn_root)
        ctx, paras, levels, models, fn_models = scan_document(doc, fn_root)

        lines = []
        lines.append(EXPORT_HEADER_V3)
        lines.append("<!-- Do not change the [N] paragraph numbers. -->")
        lines.append("<!-- ⟦N|text⟧ is a Word field, citation, cross-reference, image or equation.")
        lines.append("     Keep every token exactly once in its own paragraph (it may move within it).")
        lines.append("     The text after | is for reading only: edits inside a token are ignored. -->")
        lines.append("<!-- Lines tagged [SPECIAL] (tables of contents, lists of tables/figures)")
        lines.append("     are left untouched on import. -->")
        lines.append("<!-- Footnote references appear inline as [^N]; their text is listed at the bottom. -->")

        pages, tables = page_layout(doc) if review else (None, [])
        if review:
            lines.append("<!-- REVIEW EXPORT. 'page N' comment lines give the page on which the next")
            lines.append("     paragraph starts, as Word last laid the document out. TABLE blocks show")
            lines.append("     table text for context only: they are not imported, so table edits are")
            lines.append("     made in Word. The INVENTORY at the end lists tables, figures and other objects.")
            lines.append("     Paragraph labels and tokens are the same as in a normal export. -->")
            if pages is None:
                lines.append("<!-- NO PAGE INFORMATION: this DOCX was last saved by a program other than")
                lines.append("     Word. Open and save it in Word, then export again for page numbers. -->")
        lines.append("")

        tables_after = {}
        for n, (after, tpage, tbl) in enumerate(tables, 1):
            tables_after.setdefault(after, []).append((n, tpage, tbl))

        def emit_tables(after):
            for n, tpage, tbl in tables_after.get(after, ()):
                where = (f"page {tpage}, " if pages else "") + \
                        (f"after [{after}]" if after >= 0 else "before [0]")
                lines.append(f"<!-- TABLE {n} ({where}) - read-only, not imported")
                lines.extend(table_to_md(tbl))
                lines.append("-->")
                lines.append("")

        emit_tables(-1)
        last_page = None

        special = tokens = 0
        for i, para in enumerate(paras):
            level = levels[i]
            is_heading = level > 0
            model = models[i]

            if model is None:
                special += 1
                tag = "[SPECIAL] "
                body = legacy_para_to_markdown(para, is_heading, dict(ctx.fn_seq_map), [ctx.fn_seq_counter[0]])
            else:
                tag = ""
                body = model_to_md(model, is_heading)
                tokens += sum(isinstance(it, TokItem) for it in model.items)

            if is_heading:
                body = "#" * level + " " + body
            if not body.strip():
                body = "[Empty Paragraph]"

            if pages and pages[i] != last_page:
                lines.append(f"<!-- page {pages[i]} -->")
                lines.append("")
                last_page = pages[i]
            lines.append(f"[{i}] {tag}{body}")
            lines.append("")
            emit_tables(i)

        if ctx.fn_seq_map:
            lines.append("<!-- FOOTNOTES -->")
            lines.append("<!-- Edit the text after the colon. Do not change the [^N]: labels. -->")
            lines.append("")
            seq_to_fid = {seq: fid for fid, seq in ctx.fn_seq_map.items()}
            for seq in sorted(seq_to_fid):
                model = fn_models.get(seq)
                if model is not None:
                    text = model_to_md(model, False).strip()
                else:
                    text = "[SPECIAL] " + fn_texts.get(seq_to_fid[seq], '').strip()
                lines.append(f"[^{seq}]: {text}")
                lines.append("")

        if review:
            objects = []
            for i, model in enumerate(models):
                for it in (model.items if model is not None else ()):
                    if isinstance(it, TokItem) and it.label.startswith(OBJECT_KINDS):
                        objects.append((f"⟦{it.sym[1]}⟧", it.label, f"[{i}]", i))
                if model is None and any(True for _ in paras[i]._p.iter(w('drawing'), w('pict'))):
                    objects.append(("-", "object in a [SPECIAL] paragraph", f"[{i}]", i))
            lines.append("")
            lines.append("<!-- INVENTORY (read-only, from the DOCX)")
            lines.append(f"Tables: {len(tables)}")
            if tables:
                lines.append("| Table | Page | Position | First row |")
                lines.append("| --- | --- | --- | --- |")
                for n, (after, tpage, tbl) in enumerate(tables, 1):
                    first = tbl.find(w('tr'))
                    first = _clean_label(' / '.join(_cell_text(tc, escape=False).replace('|', '/')
                                                    for tc in first.findall(w('tc'))), 80) \
                        if first is not None else ''
                    pos = f"after [{after}]" if after >= 0 else "before [0]"
                    lines.append(f"| {n} | {tpage if pages else '?'} | {pos} | {first.replace('|', '/')} |")
            lines.append(f"Figures and other objects: {len(objects)}")
            if objects:
                lines.append("| Token | Kind | Paragraph | Page |")
                lines.append("| --- | --- | --- | --- |")
                for tok, label, para, i in objects:
                    lines.append(f"| {tok} | {label.replace('|', '/')} | {para} | {pages[i] if pages else '?'} |")
            lines.append("-->")
            lines.append("")

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"✅ Export complete: {md_path}")
        print(f"   Paragraphs: {len(paras)}, Footnotes: {len(ctx.fn_seq_map)}, "
              f"protected tokens: {tokens}, [SPECIAL]: {special}")
        if review:
            print(f"   Pages: {max(pages) if pages else 'no page information (save the DOCX in Word first)'}, "
                  f"tables: {len(tables)}")
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


def import_ai_edits(docx_path, response_path):
    try:
        doc = Document(docx_path)

        with open(response_path, 'r', encoding='utf-8') as f:
            content = f.read()
        legacy = EXPORT_HEADER_V3 not in content

        paragraphs, footnotes = parse_md(content)
        fn_root = read_footnotes_xml(docx_path)
        ctx, paras, levels, models, fn_models = scan_document(doc, fn_root, legacy=legacy)

        print(f"🔄 Applying {len(paragraphs)} paragraph edits "
              f"and {len(footnotes)} footnote edits"
              f"{' (v2 export)' if legacy else ''} …")

        changed = fn_changed = skipped_special = 0
        problems, notes_out = [], []

        for pid, text in sorted(paragraphs.items()):
            if text.lstrip().startswith('[SPECIAL]'):
                skipped_special += 1
                continue
            if pid >= len(paras):
                problems.append(f"[{pid}] exceeds document length")
                continue
            para = paras[pid]
            model = models[pid]
            text = text.strip()
            if text == '[Empty Paragraph]':
                text = ''

            heading_match = re.match(r'^(#{1,6})\s+(.*)', text, re.S)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2)
                if levels[pid] != level:
                    try:
                        para.style = f'Heading {level}'
                    except Exception:
                        pass

            if model is None or legacy:
                exported = legacy_para_to_markdown(para, levels[pid] > 0,
                                                   dict(ctx.fn_seq_map), [ctx.fn_seq_counter[0]])
            if model is None:
                # inside a multi-paragraph field (TOC, list of tables/figures)
                if md_to_plain(text) != md_to_plain(exported):
                    problems.append(f"[{pid}] is part of a table of contents / list field: "
                                    f"edit it in Word (left unchanged)")
                continue
            if legacy and text == exported.strip():
                continue        # unchanged since the v2 export

            notes = []
            ok, err = apply_text(para._p, model, text, ctx,
                                 ignore_bold=levels[pid] > 0, part=doc.part, notes=notes)
            if err:
                problems.append(f"[{pid}] left unchanged: {err}")
            elif ok:
                changed += 1
            notes_out.extend(f"[{pid}] {n}" for n in notes)

        # Footnotes
        fn_part = next((r.target_part for r in doc.part.rels.values()
                        if r.reltype == RT.FOOTNOTES), None)
        if fn_root is not None and footnotes:
            for seq, new_text in sorted(footnotes.items()):
                if seq not in fn_models or new_text.startswith('[SPECIAL]'):
                    continue
                model = fn_models[seq]
                if model is None:
                    fn = find_footnote(fn_root, {s: f for f, s in ctx.fn_seq_map.items()}[seq])
                    old_plain = ''.join(t.text or '' for t in fn.iter(W_T)).strip() if fn is not None else ''
                    if (new_text if legacy else md_to_plain(new_text)) != old_plain:
                        problems.append(f"[^{seq}] has several paragraphs: edit it in Word (left unchanged)")
                    continue
                notes = []
                ok, err = apply_text(model.p, model, new_text, ctx, plain=legacy,
                                     part=fn_part, notes=notes)
                if err:
                    problems.append(f"[^{seq}] left unchanged: {err}")
                elif ok:
                    fn_changed += 1
                notes_out.extend(f"[^{seq}] {n}" for n in notes)

        output_path = get_next_version(docx_path)
        doc.save(output_path)          # also saves new footnote link relationships

        if fn_root is not None and fn_changed:
            write_footnotes_xml(output_path, fn_root)

        print(f"✅ Import complete: {output_path}")
        print(f"   Paragraphs changed: {changed}, footnotes changed: {fn_changed}, "
              f"[SPECIAL] skipped: {skipped_special}")
        for n in notes_out:
            print(f"   ℹ️  {n}")
        if problems:
            print(f"⚠️  {len(problems)} item(s) need attention in Word:")
            for msg in problems:
                print(f"   - {msg}")

    except Exception:
        import traceback; traceback.print_exc()


def md_to_plain(text):
    return ''.join(c[0] for k, c in parse_markdown_segments(text) if k == 'text').strip()


def main():
    parser = argparse.ArgumentParser(
        description='AI Language Editor: Word <-> Markdown bridge (v3)')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--export', action='store_true',
                       help='Export DOCX to labeled Markdown')
    group.add_argument('--import', dest='import_file', metavar='RESPONSE',
                       help='Import AI-edited Markdown back into a new DOCX')
    parser.add_argument('docx', help='Source Word document (.docx)')
    parser.add_argument('--review', action='store_true',
                        help='with --export: also write page numbers, tables and a figure/table '
                             'inventory as read-only comments (<name>_for_review.md)')

    args = parser.parse_args()
    if args.review and not args.export:
        parser.error('--review only works with --export')
    if args.export:
        export_to_labeled_md(args.docx, review=args.review)
    elif args.import_file:
        import_ai_edits(args.docx, args.import_file)


if __name__ == '__main__':
    main()
