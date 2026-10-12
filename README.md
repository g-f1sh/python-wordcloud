# Python word cloud report

Count words across text files and generate a frequency report. Requires Python
3.9 or newer; no third-party packages are needed.

## Quick start

From this repository folder, run:

```powershell
python wordcloud.py samples --output report.txt
```

Five UTF-8 sample files are included. The generated report demonstrates all four
size categories and excludes words appearing once. To analyze your own folder,
replace `samples` with its path.

[Optional interactive demo](https://wordcloud.wire.fish) — paste text or upload
files to visualize the results. The Python CLI and text report are the core
deliverables; the website is an extra demonstration.

## Counting and classification

The program reads all `.txt` files directly in the selected folder, including
uppercase extensions. One thread-pool task reads one file; up to 32 workers
combine counts across the folder. Subfolders are not scanned.

The UTF-8 tab-separated report contains each retained word, its count and its
size category. Words are sorted by descending frequency, alphabetically for
ties. Words with a combined count of one are excluded.

Sizes compare each word's count with the **most frequent word's count**, not
the total number of words. Conditions are evaluated in this order:

| Condition | Size |
|---|---|
| Equal to the maximum, including ties | Huge |
| Greater than 60% of the maximum | Big |
| Otherwise greater than 30% of the maximum | Normal |
| Otherwise at or below 30% of the maximum | Small |

**Boundary assumption:** the written requirements leave exactly 30% unspecified.
This implementation assigns it to Small. Exactly 60% is Normal, following the
strict greater-than comparisons. Integer comparisons avoid floating-point
rounding at these boundaries.

For a maximum count of 10: 10 is Huge, 7 is Big, 6 and 4 are Normal, and 3 and 2
are Small. A high absolute count can still be Small when it is a low proportion
of the maximum.

## Text handling

- Input is UTF-8, with or without a BOM. Counting is case-insensitive.
- Unicode is normalized to NFC: precomposed and combining-accent spellings of
  `café` count together. Accents are preserved, so `cafe` and `café` are distinct.
- Tokens contain Unicode letters and attached combining marks. Internal straight
  and curly apostrophes are normalized. Numbers, punctuation, hyphens and
  underscores separate words.
- Common words are retained; no stop-word list is applied. Tokenization is
  character-based rather than language-aware phrase or word segmentation.

## Output and errors

An empty corpus or one containing only single occurrences produces a header
with no data rows. Missing folders, folders without text files, decoding failures
and filesystem errors produce an error and a nonzero exit code.

The output parent folder must exist. An existing output file is excluded from
input discovery, allowing repeat runs when the report is inside the input
folder. The destination is replaced atomically after successful processing.
If processing fails, any previous report remains unchanged and may be stale.
Exit codes are 0 for success, 1 for processing failure and 2 for invalid arguments.

## Verification and performance

```powershell
python -m unittest -v
python benchmark.py
```

Tests cover classification boundaries, tied maxima, Unicode normalization,
combined counts, sorting, singleton removal, repeat runs, empty input, CLI exit
codes, decoding/output errors and atomic replacement failure.

Files are processed by line and outstanding file tasks are bounded. Memory
still grows with line length, file paths and vocabulary size. Threads overlap
file I/O, but Python counting is CPU work and may not accelerate under the
standard CPython GIL. See [measured benchmark](BENCHMARK.md) for workload sizes,
results and limitations; no thread speedup is promised.

For customer use, agree on case sensitivity, accent folding, stop words,
phrases and supported languages before changing the counting policy. Frequency
and font size do not measure keyword importance or sentiment.
