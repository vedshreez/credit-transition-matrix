# Validation Write-Up: Credit Migration / Transition Matrix Model

## Summary

This project builds a discrete-time Markov chain model of corporate bond rating migration
using the cohort method, benchmarked directly against Moody's and S&P's own SEC-filed
transition studies (Form NRSRO Exhibit 1). Two validation exercises were run:

1. **Time-homogeneity test** — does a 1-year transition matrix, cubed, correctly predict
   the actual 3-year transition matrix?
2. **Macro stress test** — how differently does the same rating scale behave in a calm
   period (2024-2025) versus a real historical recession (COVID, 2019-2020)?

Both tests point to the same underlying conclusion: **the Markov / time-homogeneity
assumption is a reasonable approximation for investment-grade issuers, but breaks down
materially for speculative-grade issuers, especially under macro stress.** This is not
a modeling failure — it's a real, empirically grounded finding that mirrors what the
credit risk literature says about ratings behavior, and it's the kind of nuance a model
validator is specifically trained to look for rather than paper over.

---

## Part 1: Time-Homogeneity Test (1-Year Matrix Cubed vs. Actual 3-Year Matrix)

**Method:** Built a 1-year transition matrix for Moody's and S&P Corporate Issuers
separately, raised each to the 3rd power via matrix multiplication, and compared the
result against each agency's own *actually published* 3-year matrix for the same period.

**Result:**
- Mean absolute difference across all transition cells: **1.1 percentage points**
  (both agencies) — small in aggregate.
- The diagonal (probability of staying at the same rating) diverges much more by
  rating band:
  - **Investment grade (Aa1-Baa3):** differences mostly under 10 points; several
    categories (Aa1, Aa2) nearly exact matches.
  - **Speculative grade (Ba1, Ba3, Caa1):** differences of 9-14 points.
  - **Extreme categories (Aaa, Caa3, C):** noisiest, but these categories also have
    the smallest sample sizes (13-28 issuers), so single rating actions swing the
    percentage heavily — this is a sample-size artifact, not evidence the model is wrong.

**Interpretation:** A Markov chain assumes an issuer's next-year rating depends only on
its *current* rating, not on how it got there or what's happening in the broader economy.
That assumption holds up reasonably well for stable, investment-grade issuers, but
speculative-grade issuers behave less "memorylessly" — consistent with the idea that
distressed issuers carry momentum (a downgrade tends to predict further downgrades)
that a simple Markov structure doesn't fully capture.

---

## Part 2: Macro Stress Test (Baseline vs. COVID Recession)

**Method:** Rather than splitting a single dataset into synthetic "calm" and "stressed"
sub-periods (which the available data didn't support), this used two real, independently
published matrices for the same rating scale: the current Dec 2024-Dec 2025 baseline,
and Moody's own Dec 2019-Dec 2020 filing — a period that directly captures the COVID
market shock.

**Default probability, baseline vs. stressed:**

| Rating | Baseline Default % | Stressed Default % | Multiplier |
|---|---|---|---|
| Caa1 | 5.0% | 10.7% | 2.1x |
| Caa2 | 8.5% | 25.3% | 3.0x |
| Caa3 | 17.7% | 57.5% | 3.2x |
| Ca | 47.2% | 87.1% | 1.8x |
| C | 50.0% | 100.0% | 2.0x |

Investment-grade categories (Aaa through Baa3) show **0% default probability in both
periods** — no investment-grade issuer in this sample defaulted within one year, even
during COVID. This is a genuinely important finding: the credit-quality "floor" that
investment-grade ratings are supposed to represent held up even in a real crisis,
while speculative-grade default risk compounded sharply (roughly 2-3x) under stress.

**Downgrade rate (probability of moving to any lower non-default rating), baseline vs. stressed:**

The sharpest increases cluster in the **upper-speculative / lower-investment band**:

| Rating | Baseline | Stressed | Increase |
|---|---|---|---|
| Ba1 | 7.8% | 24.2% | +16.4 pp |
| B1 | 10.1% | 30.4% | +20.3 pp |
| Caa1 | 11.3% | 33.3% | +22.1 pp |

**A caveat worth stating plainly:** Caa2, Caa3, and Ca show *negative* changes in
downgrade rate under stress. This is not evidence that stress improved things — it's a
ceiling effect. Issuers already near the bottom of the rating scale have nowhere left
to downgrade *to* before hitting default; under acute stress they skip straight to
default rather than migrating down one notch at a time. The default-probability table
above confirms this: those same categories show the largest *default* multipliers
(3.0x-3.2x) even as their "downgrade to a lower non-default rating" numbers look
artificially calm.

---

## Key Takeaways for the Final Report

1. **Time-homogeneity is a workable simplification for investment-grade credit, not for
   speculative-grade.** Any production use of this kind of model should flag lower
   confidence in multi-year projections for sub-investment-grade portfolios.
2. **Investment-grade default risk is genuinely stable across the cycle** in this data;
   speculative-grade default risk is highly cycle-sensitive (2-3x under stress).
3. **Downgrade-rate metrics understate tail risk at the bottom of the rating scale**
   because of the ceiling/absorption effect — default probability is the more reliable
   stress indicator for the lowest categories, not downgrade rate.
4. **Sample size matters.** Categories with fewer than ~20-30 rated issuers (Aaa, Caa3,
   Ca, C) show noisy, less reliable percentages — a real constraint of publicly
   available agency data, not a flaw in the methodology.

## Data Sources

- Moody's Investors Service, Form NRSRO Exhibit 1 (filed March 2026, data through Dec
  2025; and filed March 2021, data through Dec 2020).
- S&P Global Ratings, Form NRSRO Exhibit 1 (filed March 2026, data through Dec 2025).
- Both filed with the SEC under 17 CFR 240.17g-7, publicly available via SEC EDGAR.
