#!/usr/bin/env python3
"""Normalize straight quotes to typographic (curly) quotes in a markdown file.

Two passes, order matters:
  1. Quoted spans:  "..."  ->  “...”   and   '...'  ->  ‘...’
     (must run first: the closing single quote is the same character as an
     apostrophe, so quoting uses must be resolved before apostrophes)
  2. Remaining straight apostrophes -> ’ (possessives/contractions)

Anything ambiguous is reported, not guessed.

Usage:
  python3 normalize_quotes.py input.md [output.md]
  # output defaults to <input_stem>_curly.md
"""
import re
import sys


def normalize(text):
    changes = []

    # ---- pass 1a: double-quoted spans (same line only) ----
    def sub_double(m):
        changes.append(f'DQUOTE  "{m.group(1)[:60]}" -> “{m.group(1)[:60]}”')
        return '“' + m.group(1) + '”'
    text = re.sub(r'"([^"\n]+)"', sub_double, text)

    # ---- pass 1b: single-quoted spans ----
    # opening ' must be preceded by start/space/(/[ or dash and followed by a letter;
    # closing ' is the next straight ' on the same line followed by space/punct/end.
    def sub_single(m):
        changes.append(f"SQUOTE  '{m.group(2)[:60]}' -> ‘{m.group(2)[:60]}’")
        return m.group(1) + '‘' + m.group(2) + '’' + m.group(3)
    text = re.sub(r"(^|[\s(\[–—-])'([^'\n]+?)'([\s,.;:!?\)\]]|$)",
                  sub_single, text, flags=re.M)

    # ---- report leftover unpaired double quotes, don't guess ----
    for i, line in enumerate(text.split('\n'), 1):
        if '"' in line:
            changes.append(f'WARNING line {i}: unpaired straight double quote left '
                           f'untouched -> {line.strip()[:80]}')

    # ---- pass 2: all remaining straight ' are apostrophes ----
    n_apos = text.count("'")
    text = text.replace("'", '’')
    if n_apos:
        changes.append(f'APOST   {n_apos} straight apostrophes -> ’')

    return text, changes


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src.rsplit('.', 1)[0] + '_curly.md'
    with open(src, encoding='utf-8') as fh:
        original = fh.read()
    fixed, changes = normalize(original)
    with open(dst, 'w', encoding='utf-8') as fh:
        fh.write(fixed)
    print(f'{src} -> {dst}')
    for c in changes:
        print(' ', c)
    if not changes:
        print('  no straight quotes found; file already clean')


if __name__ == '__main__':
    main()
