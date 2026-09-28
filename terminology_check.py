#!/usr/bin/env python3
"""Report terminology deviations in a translated Solterra CSV.

For every source segment (``English`` column) the script looks for terms from
``terminology.csv``. When a term occurs in the source but its approved Dutch
rendering is missing from the ``Translation`` column, the segment is reported.
Segments that follow the terminology are not written to the output.

Output columns: segment, current, should_be

    python3 terminology_check.py chapter_1.csv
    python3 terminology_check.py chapter_1.csv -t terminology.csv -o deviations.csv
    python3 terminology_check.py chapter_1.csv -t https://github.com/fdefoglio/Solterra/raw/main/terminology.csv
"""
import argparse
import csv
import html
import io
import re
import sys
import urllib.request
from collections import OrderedDict
from pathlib import Path

DEFAULT_TERMINOLOGY_URL = "https://github.com/fdefoglio/Solterra/raw/main/terminology.csv"
TAG_RE = re.compile(r"<[^>]*>")
QUOTE_MAP = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', " ": " "})


def clean(text):
    """Drop inline XML tags, unescape HTML entities, normalise quotes/whitespace."""
    text = TAG_RE.sub("", text or "")
    text = html.unescape(text)
    text = TAG_RE.sub("", text)  # tags that were entity-escaped inside <Tag>...</Tag>
    return re.sub(r"\s+", " ", text.translate(QUOTE_MAP)).strip()


def fold(text, case_sensitive):
    return text if case_sensitive else text.casefold()


def read_text(location):
    if re.match(r"https?://", location):
        with urllib.request.urlopen(location, timeout=60) as resp:
            return resp.read().decode("utf-8-sig")
    return Path(location).read_text(encoding="utf-8-sig")


def load_terminology(location):
    """Return {english: [dutch, ...]} preserving file order; duplicates merge."""
    reader = csv.DictReader(io.StringIO(read_text(location)))
    fields = {f.strip().lower(): f for f in reader.fieldnames or []}
    if "english" not in fields or "dutch" not in fields:
        sys.exit(f"{location}: expected 'english' and 'dutch' columns, found {reader.fieldnames}")
    terms = OrderedDict()
    for row in reader:
        en, nl = clean(row[fields["english"]]), clean(row[fields["dutch"]])
        if not en or not nl:
            continue
        variants = terms.setdefault(en, [])
        if nl not in variants:
            variants.append(nl)
    return terms


def build_matchers(terms, case_sensitive):
    """Compile one whole-word regex per English term, longest term first.

    Merges entries that only differ by case (unless --case-sensitive) so that a
    term with several approved renderings accepts any of them.
    """
    merged = OrderedDict()
    for en, nls in terms.items():
        key = fold(en, case_sensitive)
        entry = merged.setdefault(key, (en, []))
        for nl in nls:
            if nl not in entry[1]:
                entry[1].append(nl)
    matchers = []
    for en, nls in merged.values():
        pattern = r"(?<!\w)" + r"\s+".join(re.escape(w) for w in en.split()) + r"(?!\w)"
        flags = 0 if case_sensitive else re.IGNORECASE
        matchers.append((en, nls, re.compile(pattern, flags)))
    matchers.sort(key=lambda m: len(m[0]), reverse=True)
    return matchers


def find_deviations(source, target, matchers, case_sensitive):
    """Yield (term, approved_dutch_list) for each term that is absent in target."""
    covered = []  # source spans already claimed by a longer term
    folded_target = fold(target, case_sensitive)
    for en, nls, rx in matchers:
        for m in rx.finditer(source):
            if any(m.start() < e and s < m.end() for s, e in covered):
                continue  # part of a longer term that was already checked
            covered.append(m.span())
            if not any(fold(nl, case_sensitive) in folded_target for nl in nls):
                yield en, nls
            break  # one check per term per segment is enough


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="translated CSV (columns English, Translation)")
    ap.add_argument("-t", "--terminology", default=None,
                    help="terminology CSV path or URL (default: ./terminology.csv next to the "
                         "script, else the GitHub raw URL)")
    ap.add_argument("-o", "--output", default=None, help="output CSV (default: <input>_deviations.csv)")
    ap.add_argument("--source-col", default="English")
    ap.add_argument("--target-col", default="Translation")
    ap.add_argument("--case-sensitive", action="store_true",
                    help="treat capitalisation differences as deviations")
    ap.add_argument("--min-words", type=int, default=1,
                    help="only check terms with at least this many words; use 2 to skip generic "
                         "single-word terms that Dutch often merges into compounds (default: 1)")
    ap.add_argument("--detailed", action="store_true",
                    help="add RowIndex and term columns to the output")
    args = ap.parse_args()

    term_loc = args.terminology
    if term_loc is None:
        local = Path(__file__).with_name("terminology.csv")
        term_loc = str(local) if local.exists() else DEFAULT_TERMINOLOGY_URL
    terms = load_terminology(term_loc)
    matchers = [m for m in build_matchers(terms, args.case_sensitive)
                if len(m[0].split()) >= args.min_words]

    out_path = Path(args.output) if args.output else Path(args.input).with_name(Path(args.input).stem + "_deviations.csv")
    columns = ["segment", "current", "should_be"]
    if args.detailed:
        columns = ["RowIndex", "term"] + columns

    seen, deviations, total = set(), [], 0
    with open(args.input, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for col in (args.source_col, args.target_col):
            if col not in (reader.fieldnames or []):
                sys.exit(f"{args.input}: column '{col}' not found, found {reader.fieldnames}")
        for i, row in enumerate(reader, start=1):
            source, target = clean(row[args.source_col]), clean(row[args.target_col])
            if not source:
                continue
            total += 1
            for en, nls in find_deviations(source, target, matchers, args.case_sensitive):
                rec = {"RowIndex": row.get("RowIndex", i), "term": en,
                       "segment": source, "current": target, "should_be": " | ".join(nls)}
                key = (source, target, rec["should_be"])
                if key in seen:
                    continue
                seen.add(key)
                deviations.append(rec)

    with open(out_path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, quoting=csv.QUOTE_ALL, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(deviations)

    print(f"Checked {total} segments against {len(terms)} terms: "
          f"{len(deviations)} deviation(s) -> {out_path}")


if __name__ == "__main__":
    main()
