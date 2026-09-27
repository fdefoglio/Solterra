#!/usr/bin/env python3
"""Unzip the Solterra skill and combine every file it contains into one Markdown file.

Files are written one after the other, SKILL.md first, then the rest in
archive order. Markdown files are inserted as-is; every other file is wrapped
in a fenced code block.

Usage:
    python skill_to_md.py [ZIP] [-o OUTPUT.md] [-x EXTRACT_DIR]
"""

import argparse
import re
import zipfile
from pathlib import Path

LANGUAGES = {
    ".py": "python",
    ".csv": "csv",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sh": "bash",
    ".txt": "text",
}


def fence_for(text):
    """Return a backtick fence longer than any backtick run inside the text."""
    longest = max((len(m) for m in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def ordered_members(archive):
    files = [info for info in archive.infolist() if not info.is_dir()]
    # SKILL.md goes first; everything else keeps its archive order.
    return sorted(files, key=lambda info: Path(info.filename).name != "SKILL.md")


def read_text(data):
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


def build_markdown(zip_path):
    with zipfile.ZipFile(zip_path) as archive:
        members = ordered_members(archive)
        parts = [f"# {zip_path.stem}\n", "## Contents\n"]
        parts += [f"{i}. `{m.filename}`" for i, m in enumerate(members, 1)]
        parts.append("")

        for member in members:
            name = member.filename
            parts.append(f"\n---\n\n## File: `{name}`\n")
            text = read_text(archive.read(member))
            if text is None:
                parts.append(f"_Binary file ({member.file_size} bytes) - content not included._\n")
                continue
            text = text.rstrip("\n")
            suffix = Path(name).suffix.lower()
            if suffix == ".md":
                parts.append(text + "\n")
            else:
                fence = fence_for(text)
                parts.append(f"{fence}{LANGUAGES.get(suffix, '')}\n{text}\n{fence}\n")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("zip", nargs="?", default="solterra-batch-translation.zip",
                        help="skill archive (default: %(default)s)")
    parser.add_argument("-o", "--output", help="output Markdown file (default: <zip name>.md)")
    parser.add_argument("-x", "--extract-dir", default=".",
                        help="directory to unzip the skill into (default: current directory)")
    args = parser.parse_args()

    zip_path = Path(args.zip)
    output = Path(args.output) if args.output else zip_path.with_suffix(".md")

    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(args.extract_dir)
    print(f"Extracted {zip_path} into {Path(args.extract_dir).resolve()}")

    output.write_text(build_markdown(zip_path), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
