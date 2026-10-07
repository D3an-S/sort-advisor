# Sort Advisor

A web tool that analyzes a column of a CSV file and recommends the most suitable sorting algorithm, with a clear explanation why.

Built as a student project at DHBW. The core idea: there is no single best sorting algorithm. The right choice depends on the data.

## Features
- Upload a CSV file and pick any column (numbers or text)
- Analyzes data properties: size, presortedness, duplicate ratio, data type
- Recommends an algorithm based on rules from the literature
- Explains each recommendation

## Getting started
```
git clone https://github.com/DeanS-carthago/sort-advisor.git
cd sort-advisor
python -m venv .venv
.venv\Scripts\activate  
pip install -r requirements.txt
streamlit run app.py
```
## Project structure
| File | Purpose |
|------|---------|
| app.py | Streamlit UI: upload, column selection, output |
| analysis.py | Computes data properties |
| rules.py | Decision rules for the recommendation |

## Security
Uploads are limited to 5 MB and 100,000 rows, processed in memory only and never stored.

