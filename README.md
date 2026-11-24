# Sort Advisor

A web tool that analyzes one column of a CSV file and recommends the fastest suitable sorting algorithm, with a clear explanation why.

[![Open Sort Advisor in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://sort-advisor-wds225.streamlit.app/)

Built as a student project at DHBW Ravensburg (Theoretical Computer Science, Group 05). The core idea: there is no single best sorting algorithm. The right choice depends on the data and on what you need from the result.

## Features

- Upload a CSV file and pick any column (numbers or text)
- Computes eight data properties, including size, number of inversions, runs and duplicate ratio
- Recommends Insertion, Merge, Quick or Heap Sort and explains the rule that applied
- Optional requirements: stable sorting and/or limited memory
- Live comparison: runs all four algorithms on your data and shows the runtimes

## How the recommendation works

The rules are checked in this order, the first match wins:

| # | Condition | Recommendation |
|---|-----------|----------------|
| 1 | n ≤ 16 or Inv / (n · log₂ n) ≤ 0.5 | Insertion Sort |
| 2 | Stability required | Merge Sort |
| 3 | Limited memory | Heap Sort |
| 4 | Otherwise | Quick Sort |

The thresholds 16 and 0.5 were determined by our own measurements with the implementations in `sorting.py`.

## Getting started

```bash
git clone https://github.com/D3an-S/sort-advisor.git
cd sort-advisor
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py
```

macOS / Linux:
```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

## Project structure

| File | Purpose |
|------|---------|
| `app.py` | Streamlit UI: upload, column selection, recommendation, live comparison |
| `analysis.py` | Computes the data properties, counts inversions in O(n log n) |
| `rules.py` | Decision rules and the explanation text |
| `sorting.py` | Insertion, Merge, Quick and Heap Sort in pure Python |
| `test_analysis.py`, `test_rules.py` | Unit tests for analysis and rules |
| `benchmarks/benchmark.py` | Runtime measurements used in the project report |
| `make_security_tests.py` | Generates the synthetic files for the security tests |
| `.streamlit/config.toml` | Upload limit and security settings |

## Running the tests

```bash
pip install pytest
pytest
```

## Security

- Uploads are limited to 5 MB, only CSV, at most 100,000 rows are read
- Files are processed in memory only and never stored
- No `eval`/`exec`, no `unsafe_allow_html`: uploaded content is always shown as text
- Error details and data export are disabled in the UI
- No caching, so sessions never share data
- Dependency versions are pinned in `requirements.txt`

`make_security_tests.py` creates nine test files (script code in column names, oversized files, binary data and more) to check these measures manually.

## Release

The state at the submission of the project report is tagged as [`v1.0`](https://github.com/D3an-S/sort-advisor/releases/tag/v1.0).
