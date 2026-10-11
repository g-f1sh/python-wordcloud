# Python word cloud report

Requires Python 3.9 or newer. No third-party packages are needed.

Run from this project folder:

```powershell
python wordcloud.py samples --output report.txt
python -m unittest -v
```

The program reads all `.txt` files directly in the chosen folder, including uppercase extensions. It submits one task per file to a thread pool (at most 32 workers), merges their word counts, excludes words with a combined count of one, and writes a UTF-8 tab-separated report. The demonstration uses five files; the program also accepts smaller folders. Subfolders are not scanned.

## Decisions

- Words are case-insensitive Unicode letter sequences; internal apostrophes are retained and curly apostrophes normalized. Numbers are ignored, and hyphens and underscores separate words. Common words are counted; no stop-word list is applied.
- Counts are sorted descending, with alphabetical ordering for ties.
- Every word tied for maximum frequency is Huge.
- Big means strictly greater than 60% of the maximum count; Normal means strictly greater than 30% after checking Big. Remaining words are Small.
- Exactly 30% is classified as Small; exactly 60% is Normal.
- Integer comparisons avoid floating-point rounding at threshold boundaries.
- An empty corpus or one containing only single occurrences produces the header with no data rows.
- Missing folders, folders without text files, decoding failures, and filesystem errors produce an error and nonzero exit status. Input must be UTF-8 (with or without a BOM), and the output's parent folder must already exist.
- An existing output file is excluded from input discovery, allowing repeat runs when the report is inside the input folder. Choose a dedicated output filename; it will be overwritten.

## How it works

`count_file` reads and counts one file. `build_report` combines the returned counters in the main thread, so workers do not modify shared counts. `font_size` classifies each retained word relative to the maximum, rather than relative to the total word count.

The sample has a maximum of 10. Its report demonstrates Huge (10), Big (7), Normal (6 and 4), Small (3 and 2), and exclusion of a singleton.

Tests cover threshold boundaries, tied maxima, tokenization, counts combined across files, sorting, singleton removal, repeat runs, empty input, and invalid folders.
