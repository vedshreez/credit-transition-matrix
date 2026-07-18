# Credit Migration / Transition Matrix Model

A cohort-method Markov chain model of corporate bond rating migration, benchmarked against Moody's and S&P's own published transition studies, with macro stress-testing to compare baseline vs. recession-era downgrade and default behavior.

---

## Introduction

Credit rating transition matrices describe how a bond issuer's credit rating evolves over time — for example, the probability that a BBB-rated issuer is still BBB, or has been upgraded to A, downgraded to BB, or defaulted, one year later. This project builds that model from scratch using the same cohort methodology that Moody's and S&P themselves use to publish their own annual transition studies, then validates the results directly against those published numbers.

A Markov chain is a natural fit here: an issuer's next rating depends only on its current rating, not its full history, and default is treated as an "absorbing state" — once an issuer defaults, it doesn't transition out. This structure lets multi-year transition probabilities be derived directly from a single one-year matrix through matrix multiplication, which is the core mechanic this project implements and tests.

## Motivation

Rating transition matrices sit at the center of a surprisingly wide range of real-world work: rating agencies publish them as their core credibility artifact every year, banks use them to estimate probability of default (PD) for regulatory capital and CECL/IFRS 9 credit loss provisioning, and model validation teams routinely re-derive and stress an internal transition matrix as a benchmark check against the agency-published version.

Despite that, very few student-level projects touch credit migration modeling directly — most cluster around market risk topics like VaR, options pricing, or volatility. That makes this project a meaningful differentiator for roles in rating agencies, bank credit risk teams, and model validation groups, while staying lightweight enough (compared to a full market-risk pipeline) to build and validate properly in a short timeframe.

## What this project does

1. **Sources real transition data** directly from both major rating agencies' SEC filings (not third-party estimates) — Moody's and S&P are legally required to publish 1-year, 3-year, and 10-year transition and default rate matrices annually as Exhibit 1 to their Form NRSRO filing on SEC EDGAR.
2. **Extracts those matrices cleanly** from the source PDFs using position-aware table parsing, preserving every cell (including implicit zeros) rather than relying on flattened text.
3. **Validates the matrices structurally** — confirming each row of probabilities sums to ~100%, and cross-checking Moody's vs. S&P behavior at equivalent rating levels.
4. **(Next phase) Applies macro stress-testing** — splitting the historical sample into recession vs. expansion periods to produce a baseline-vs-stressed comparison of downgrade and default rates by rating category, in the style used in bank CCAR/DFAST submissions.

## Data

All data comes from a genuinely public, free source: **SEC Form NRSRO Exhibit 1 filings**. Every Nationally Recognized Statistical Rating Organization (NRSRO) — including Moody's and S&P — is required by SEC rule to publish these transition/default tables annually, broken out by asset class (corporate issuers, financial institutions, insurance companies, structured finance, sovereigns, etc.) and by horizon (1-year, 3-year, 10-year).

This project uses each agency's most recent filing, covering the period through December 31, 2025:

- **Moody's**: [Form NRSRO Exhibit 1, filed March 2026](https://www.sec.gov/Archives/edgar/data/1698547/000119312526133970/d113944dex99e1nrsro.pdf)
- **S&P Global Ratings**: [Form NRSRO Exhibit 1, filed March 2026](https://www.sec.gov/Archives/edgar/data/1650548/000165054826000001/Ex1_Mar2026.pdf)

### `data/` folder contents

| File | Description |
|---|---|
| `moodys_corporate_1y.csv` | Moody's Corporate Issuers, 1-year transition/default rates (Dec 2024 → Dec 2025) |
| `moodys_corporate_3y.csv` | Moody's Corporate Issuers, 3-year transition/default rates (Dec 2022 → Dec 2025) |
| `moodys_corporate_10y.csv` | Moody's Corporate Issuers, 10-year transition/default rates (Dec 2015 → Dec 2025) |
| `sp_corporate_1y.csv` | S&P Corporate Issuers, 1-year transition/default rates (Dec 2024 → Dec 2025) |
| `sp_corporate_3y.csv` | S&P Corporate Issuers, 3-year transition/default rates (Dec 2022 → Dec 2025) |
| `sp_corporate_10y.csv` | S&P Corporate Issuers, 10-year transition/default rates (Dec 2015 → Dec 2025) |
| `raw/moodys_exhibit1_2026.pdf` | Original Moody's source filing, kept for provenance/audit |
| `raw/sp_exhibit1_2026.pdf` | Original S&P source filing, kept for provenance/audit |

Each CSV has one row per starting rating (e.g., `Aaa`, `Baa2`, `Caa1`), the number of rated issuers that started in that category (`n_outstanding`), and one column per possible ending outcome — every other rating category, plus `Default`, `Paid Off`, and `Withdrawn (other)` — expressed as a percentage.

Note: row sums land in the 98–102% range rather than exactly 100%, because each cell is independently rounded to the nearest 1% in the source filings. This is expected and matches the original published tables, not a parsing error.

### `src/` folder contents

| File | Description |
|---|---|
| `extract_matrices.py` | Extracts the Corporate Issuers transition/default tables from both agencies' raw Exhibit 1 PDFs into the clean CSVs in `data/`, using `pdfplumber` for position-aligned table parsing (so blank/implicit-zero cells are read correctly rather than dropped, which is a common failure mode of naive text extraction from these filings). |

## Methodology (in progress)

1. **Cohort-method construction** — for each starting rating, count how many issuers migrated to each other rating (or defaulted) over a fixed horizon, divide by the starting count to get transition probabilities. This is the exact method Moody's and S&P themselves describe using in their own filings.
2. **Multi-year transitions via matrix power** — the n-year transition matrix is the one-year matrix raised to the n-th power, under a time-homogeneity assumption that will be tested rather than simply assumed.
3. **Macro stress-testing** — splitting the historical sample into recession vs. expansion periods (via NBER recession dates or a GDP-growth threshold) to produce baseline vs. stressed transition matrices.
4. **Validation** — comparing any independently reconstructed matrix against these published agency benchmarks, and investigating any material divergence rather than treating agreement as automatic.

## References

- Jarrow, R. A., Lando, D., & Turnbull, S. M. (1997). *A Markov Model for the Term Structure of Credit Risk Spreads.* Review of Financial Studies, 10(2), 481–523.
- Moody's Investors Service, Form NRSRO Exhibit 1 (Credit Ratings Performance Measurement Statistics).
- S&P Global Ratings, Form NRSRO Exhibit 1 (Ratings Performance Measurement Statistics).
- Federal Reserve, CCAR / Dodd-Frank Act Stress Test (DFAST) scenario documentation.
