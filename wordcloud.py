"""Create a frequency report from text files using only Python's standard library."""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re


def count_file(path: Path) -> Counter:
    """Read one UTF-8 file and count case-insensitive Unicode words."""
    text = path.read_text(encoding="utf-8-sig")
    words = re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)*", text)
    return Counter(word.casefold().replace("’", "'") for word in words)


def font_size(count: int, maximum: int) -> str:
    """Use integer comparisons to avoid rounding percentage boundaries."""
    if count == maximum:
        return "Huge"
    if count * 100 > maximum * 60:
        return "Big"
    if count * 100 > maximum * 30:
        return "Normal"
    return "Small"


def build_report(folder: Path, output: Path) -> int:
    """Combine per-file counts and write a tab-separated report."""
    if not folder.is_dir():
        raise ValueError(f"Input folder does not exist: {folder}")
    files = sorted(
        path for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() == ".txt"
        and path.resolve() != output.resolve()
    )
    if not files:
        raise ValueError(f"No text files found in: {folder}")

    counts = Counter()
    # Each submitted task reads exactly one file. Only the main thread merges.
    with ThreadPoolExecutor(max_workers=min(32, len(files))) as executor:
        for file_counts in executor.map(count_file, files):
            counts.update(file_counts)

    maximum = max(counts.values(), default=0)
    rows = sorted(
        ((word, count) for word, count in counts.items() if count > 1),
        key=lambda item: (-item[1], item[0]),
    )
    lines = ["word\tcount\tfont_size"]
    lines.extend(
        f"{word}\t{count}\t{font_size(count, maximum)}" for word, count in rows
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(files)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="Folder containing UTF-8 .txt files")
    parser.add_argument("-o", "--output", type=Path, default=Path("report.txt"))
    args = parser.parse_args()
    try:
        file_count = build_report(args.folder, args.output)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Read {file_count} files. Report saved to {args.output}")


if __name__ == "__main__":
    main()
