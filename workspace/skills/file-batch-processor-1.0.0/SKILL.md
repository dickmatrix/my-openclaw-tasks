---
name: File Batch Processor
description: Batch processes local files including PDF text extraction, Excel/CSV reading and merging, format conversion, and data cleaning. Returns summary results instead of raw content to minimize token usage. Use when the user needs to process multiple files, convert PDFs, merge spreadsheets, or clean datasets.
read_when:
  - Processing or extracting text from PDF files
  - Reading, merging, or cleaning Excel/CSV files
  - Batch converting or summarizing local documents
  - Cleaning or deduplicating tabular data
metadata: {"clawdbot":{"emoji":"📂"}}
---

# File Batch Processor Skill

Processes PDF, Excel, CSV files in bulk. Key principle: **return summaries, not raw content** — keeps token usage low regardless of file size.

## Setup

```bash
pip install pdfplumber openpyxl pandas
```

## PDF — Extract text

```python
import pdfplumber
from pathlib import Path

def extract_pdfs(paths: list[str]) -> list[dict]:
    results = []
    for path in paths:
        with pdfplumber.open(path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        results.append({
            "file": Path(path).name,
            "pages": len(pdf.pages),
            "chars": len(text),
            "preview": text[:200]
        })
    return results
```

## PDF — Extract tables

```python
with pdfplumber.open("file.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        for table in page.extract_tables():
            print(f"Page {i+1}: {len(table)} rows")
```

## Excel / CSV — Summarize

```python
import pandas as pd

def summarize_file(path: str) -> dict:
    df = pd.read_excel(path) if path.endswith('.xlsx') else pd.read_csv(path)
    return {
        "file": path,
        "rows": len(df),
        "columns": list(df.columns),
        "nulls": df.isnull().sum().to_dict(),
        "sample": df.head(3).to_dict(orient="records")
    }
```

## Merge multiple CSVs

```python
import glob, pandas as pd

files = glob.glob("data/*.csv")
merged = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
merged.to_csv("merged_output.csv", index=False)
print(f"Merged {len(files)} files → {len(merged)} rows")
```

## Clean data

```python
def clean_df(df):
    df = df.dropna(how="all").drop_duplicates()
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df
```

## Output convention

Always return summary dict:
```python
{"processed": 42, "failed": 1, "total_rows": 15830, "output_file": "merged_output.csv"}
```
