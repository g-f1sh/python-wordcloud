# Counting benchmark

Measured on 12 October 2026 with `python benchmark.py` after the Unicode, streaming and bounded-submission changes.

Environment: CPython 3.12.14, Windows 11 build 26300, AMD64, 14 reported logical CPUs. Inputs were synthetic UTF-8 files on the local filesystem. Each condition ran three times, alternating serial/threaded order. Both paths used the same tokenizer and matched exact expected counts.

| Workload | Files | Total bytes | Distinct words | Total words | Workers | Serial median | Threads median |
|---|---:|---:|---:|---:|---:|---:|---:|
| Many small files | 1,000 | 1,800,000 | 257 | 257,000 | 32 | 0.519 s | 0.536 s |
| Five larger files | 5 | 1,350,000 | 257 | 192,750 | 5 | 0.183 s | 0.183 s |

Threads did not show a speed advantage in these measurements. They satisfy parallel file reading; local cache behavior and CPU tokenization can dominate these small workloads. This result does not predict performance on network storage or significantly larger files.

The measurement covers counting and aggregation only, excluding report writing. Filesystem caches were not cleared, storage hardware was not characterized, and peak memory was not measured. The 1,000-file condition is a small-file smoke benchmark, not proof of large-file scalability. The permanent test suite additionally checks a 50,000-line input but is not a capacity benchmark.

Reproduce: `python benchmark.py`. Generated fixtures are temporary and removed automatically. Timings vary by environment; correctness is checked on every repetition. A process-pool comparison is outside this assignment's scope.
