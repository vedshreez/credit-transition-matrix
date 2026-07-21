"""
Extracts Corporate Issuers rating transition matrices (1/3/10-year) from
Moody's and S&P Form NRSRO Exhibit 1 filings into clean CSVs.

Source PDFs (SEC EDGAR):
  Moody's: https://www.sec.gov/Archives/edgar/data/1698547/000119312526133970/d113944dex99e1nrsro.pdf
  S&P:     https://www.sec.gov/Archives/edgar/data/1650548/000165054826000001/Ex1_Mar2026.pdf
"""
import pdfplumber
import pandas as pd
import re
import os

OUT_DIR = "data"
os.makedirs(OUT_DIR, exist_ok=True)

def clean_pct(val):
    if val is None or val == "":
        return 0.0
    return float(val.strip().replace("%", ""))

def table_to_df(table):
    # Find the header row dynamically (first cell starts with "Credit")
    header_idx = next(
        i for i, r in enumerate(table)
        if r[1] and "Number" in r[1].replace("\n", " ")
    )
    header = table[header_idx]
    cols = [c.replace("\n", " ") if c else c for c in header]
    rows = []
    for r in table[header_idx + 1:]:
        if not r[0] or r[0] in (None, "") or r[0].strip().lower() == "total":
            continue
        rating = r[0]
        n_outstanding = r[1]
        if n_outstanding in (None, "", "-"):
            continue
        values = [clean_pct(v) for v in r[2:]]
        row = {"starting_rating": rating, "n_outstanding": int(n_outstanding.replace(",", ""))}
        for col_name, v in zip(cols[2:], values):
            row[col_name] = v
        rows.append(row)
    return pd.DataFrame(rows)

def extract(pdf_path, page_indices, labels, prefix):
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, label in zip(page_indices, labels):
            page = pdf.pages[page_idx]
            tables = page.extract_tables()
            table = tables[0]
            df = table_to_df(table)
            out_path = f"{OUT_DIR}/{prefix}_corporate_{label}.csv"
            df.to_csv(out_path, index=False)
            print(f"Wrote {out_path}  ({len(df)} rating rows)")

if __name__ == "__main__":
    # Moody's: page 4 has BOTH 1yr and 3yr tables (two tables on one page), page 5 has 10yr
    with pdfplumber.open("/mnt/user-data/uploads/d113944dex99e1nrsro.pdf") as pdf:
        page4_tables = pdf.pages[4].extract_tables()
        df_1y = table_to_df(page4_tables[0])
        df_3y = table_to_df(page4_tables[1])
        df_1y.to_csv(f"{OUT_DIR}/moodys_corporate_1y.csv", index=False)
        df_3y.to_csv(f"{OUT_DIR}/moodys_corporate_3y.csv", index=False)
        print(f"Wrote moodys_corporate_1y.csv ({len(df_1y)} rows)")
        print(f"Wrote moodys_corporate_3y.csv ({len(df_3y)} rows)")

        page5_tables = pdf.pages[5].extract_tables()
        df_10y = table_to_df(page5_tables[0])
        df_10y.to_csv(f"{OUT_DIR}/moodys_corporate_10y.csv", index=False)
        print(f"Wrote moodys_corporate_10y.csv ({len(df_10y)} rows)")

    # S&P: pages 8, 9, 10 each have one table (1yr, 3yr, 10yr respectively)
    extract(
        "/mnt/user-data/uploads/Ex1_Mar2026.pdf",
        page_indices=[8, 9, 10],
        labels=["1y", "3y", "10y"],
        prefix="sp",
    )
