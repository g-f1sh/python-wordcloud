"""Reproducible smoke benchmark; reports measurements, not a promised speedup."""

from collections import Counter
import json
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import time

from wordcloud import combine_files, count_file


def serial(files):
    result = Counter()
    for path in files:
        result.update(count_file(path))
    return result


def run():
    measurements = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        # Alphabetic identifiers exercise a fixed, nontrivial vocabulary.
        vocabulary = ["term" + chr(97 + i // 26) + chr(97 + i % 26) for i in range(257)]
        line = " ".join(vocabulary) + "\n"
        for label, file_count, repeats in [("many small files", 1000, 1),
                                            ("five larger files", 5, 150)]:
            folder = root / label
            folder.mkdir()
            for i in range(file_count):
                (folder / f"{i:04}.txt").write_text(line * repeats, encoding="utf-8")
            files = sorted(folder.iterdir())
            timings = {"serial": [], "threads": []}
            expected = {word: file_count * repeats for word in vocabulary}
            for repetition in range(3):
                # Alternate order to reduce consistent warm-cache bias.
                order = [("serial", serial), ("threads", combine_files)]
                if repetition % 2:
                    order.reverse()
                for name, function in order:
                    start = time.perf_counter()
                    result = function(files)
                    timings[name].append(time.perf_counter() - start)
                    assert dict(result) == expected
            measurements.append({
                "workload": label, "files": file_count,
                "total_bytes": sum(path.stat().st_size for path in files),
                "vocabulary": len(vocabulary), "words": file_count * repeats * len(vocabulary),
                "repetitions": 3, "workers": min(32, file_count),
                "seconds": timings,
                "median_seconds": {k: statistics.median(v) for k, v in timings.items()},
            })
    return {"python": sys.version.split()[0], "platform": platform.platform(),
            "architecture": platform.machine(), "logical_cpus": __import__('os').cpu_count(),
            "measurements": measurements,
            "limitations": "Synthetic local files, warm/mixed filesystem caches; counting only. "
            "No report-writing or memory benchmark. Not a production capacity or speedup guarantee."}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
