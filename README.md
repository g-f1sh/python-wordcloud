# Python word cloud report

Requires Python 3.9 or newer. No third-party packages are needed.

Run from this project folder:

```powershell
python wordcloud.py samples --output report.txt
python -m unittest -v
```

The program reads all `.txt` files directly in the chosen folder, including uppercase extensions. It submits one task per file to a thread pool (at most 32 workers), merges their word counts, excludes words with a combined count of one, and writes a UTF-8 tab-separated report. The demonstration uses five files; the program also accepts smaller folders. Subfolders are not scanned.

## Decisions

- UTF-8 text is normalized to NFC, so precomposed `café` and decomposed `café` aggregate together. Tokens contain Unicode letters and combining marks attached to them. Case folding is applied, and internal straight/curly apostrophes are normalized. Unicode numbers (including `²`), punctuation, hyphens and underscores separate words. This is character-based tokenization, not language-aware segmentation; languages without spaces may produce long tokens. Common words are counted; no stop-word list is applied.
- Counts are sorted descending, with alphabetical ordering for ties.
- Every word tied for maximum frequency is Huge.
- Big means strictly greater than 60% of the maximum count; Normal means strictly greater than 30% after checking Big. Remaining words are Small.
- Exactly 30% is classified as Small; exactly 60% is Normal.
- The assignment example differs from the written threshold rules at exactly 60% and 30%. This implementation follows the strict greater-than comparisons and assigns remaining nonmaximum counts to Small. Boundary behavior is documented and tested; it was an explicit interpretation, not a change to match the visual example.
- Integer comparisons avoid floating-point rounding at threshold boundaries.
- An empty corpus or one containing only single occurrences produces the header with no data rows.
- Missing folders, folders without text files, decoding failures, and filesystem errors produce an error and nonzero exit status. Input must be UTF-8 (with or without a BOM), and the output's parent folder must already exist.
- An existing output file is excluded from input discovery, allowing repeat runs when the report is inside the input folder. Choose a dedicated output filename; it will be overwritten.
- A report is written to a temporary file beside the destination, then replaced atomically. Input, writing, or replacement failures do not intentionally publish partial results. The CLI names unreadable inputs and warns that any previous report remains unchanged and may be stale. Consumers must check the exit code: 0 success, 1 processing failure, 2 invalid CLI arguments. No crash-durability guarantee is made for all filesystems.

## How it works

`count_file` reads and counts one file by line, without building a whole-file token list. `build_report` combines local counters in the main thread. Submission is bounded to at most 32 outstanding file tasks, rather than queuing the entire corpus. Worker threads are reused; one task still reads exactly one file. `font_size` compares each retained word with the maximum aggregate count, not total words.

Memory still grows with the longest line, concurrent per-file vocabularies, discovered file paths, aggregate vocabulary, and sorted output rows. This is not fixed-memory processing or a claim of support for arbitrary input sizes. One extremely long line or large vocabulary can still be expensive.

Threads can overlap file I/O, but Python tokenization/counting is CPU work and may not accelerate under the standard CPython GIL. No thread speedup is promised. See [measured benchmark](BENCHMARK.md) for this implementation, workload sizes, and limitations. The CLI is the assignment deliverable; a separately hosted website is an optional demonstration.

The sample has a maximum of 10. Its report demonstrates Huge (10), Big (7), Normal (6 and 4), Small (3 and 2), and exclusion of a singleton.

Tests cover threshold boundaries, tied maxima, canonical Unicode and numeric characters, combined counts, sorting, singleton removal, repeat runs, empty input, a larger multiline file, CLI exit codes, decoding/output failures, and atomic replacement failure. Failure tests verify the old destination is preserved and temporary output is cleaned up.

Reproduce the benchmark with `python benchmark.py`. Its serial baseline uses the same tokenizer to isolate scheduling differences. It checks counts, alternates execution order and reports three-run medians. It measures synthetic local-file counting, not memory, network storage or the web service.
