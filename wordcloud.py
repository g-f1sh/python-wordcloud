"""Create a frequency report from text files using only Python's standard library."""

import argparse
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import os
from pathlib import Path
import tempfile
import unicodedata


def words_in_line(line: str):
    """Yield NFC words made of letters, attached marks and internal apostrophes."""
    line = unicodedata.normalize("NFC", line)
    token = []
    for index, character in enumerate(line):
        category = unicodedata.category(character)
        if category.startswith("L") or (token and category.startswith("M")):
            token.append(character)
        elif (character in "'’" and token and index + 1 < len(line)
              and unicodedata.category(line[index + 1]).startswith("L")):
            token.append("'")
        else:
            if token:
                yield unicodedata.normalize("NFC", "".join(token).casefold())
                token = []
    if token:
        yield unicodedata.normalize("NFC", "".join(token).casefold())


def count_file(path: Path) -> Counter:
    """Count one UTF-8 file by line without building a whole-file token list."""
    counts = Counter()
    try:
        with path.open(encoding="utf-8-sig") as source:
            for line in source:
                counts.update(words_in_line(line))
    except (OSError, UnicodeError) as error:
        raise ValueError(f"Cannot read input file {path}: {error}") from error
    return counts


def combine_files(files, workers: int = 32) -> Counter:
    """Keep at most one outstanding file task per worker, merging as they finish."""
    counts = Counter()
    paths = iter(files)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        pending = {executor.submit(count_file, path)
                   for path in [next(paths, None) for _ in range(workers)]
                   if path is not None}
        while pending:
            completed, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in completed:
                counts.update(future.result())
            completed.clear()  # Release per-file results before submitting more.
            for _ in range(workers - len(pending)):
                path = next(paths, None)
                if path is None:
                    break
                pending.add(executor.submit(count_file, path))
    return counts


def write_report(output: Path, rows, maximum: int) -> None:
    """Publish a complete report by replacing the destination atomically."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=output.parent,
            prefix=".wordcloud-", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write("word\tcount\tfont_size\n")
            for word, count in rows:
                stream.write(f"{word}\t{count}\t{font_size(count, maximum)}\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


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

    # Each submitted task reads exactly one file. Only the main thread merges.
    counts = combine_files(files, workers=min(32, len(files)))

    maximum = max(counts.values(), default=0)
    rows = sorted(
        ((word, count) for word, count in counts.items() if count > 1),
        key=lambda item: (-item[1], item[0]),
    )
    write_report(output, rows, maximum)
    return len(files)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="Folder containing UTF-8 .txt files")
    parser.add_argument("-o", "--output", type=Path, default=Path("report.txt"))
    args = parser.parse_args()
    try:
        file_count = build_report(args.folder, args.output)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(1, f"Error: {error}\nNo new report was published. "
                    "Any previous report remains unchanged and may be stale.\n")
    print(f"Read {file_count} files. Report saved to {args.output}")


if __name__ == "__main__":
    main()
