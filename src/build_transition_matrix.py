"""
Builds a proper Markov chain transition matrix from the extracted benchmark
CSVs, and validates the time-homogeneity assumption by squaring/cubing the
1-year matrix and comparing it against the agency's own published 3-year
matrix.

Modeling choice (documented, not hidden):
  "Paid Off" and "Withdrawn (other)" are excluded from the Markov state
  space and each row is renormalized over {ratings, Default} only. This is
  a standard simplification in the credit transition literature: paid-off
  and withdrawn-for-other-reasons exits are not credit events, and without
  this adjustment the matrix cannot be squared to produce a valid multi-year
  transition matrix (the rows would not represent a closed system).
  This assumption is exactly the kind of thing Day 5's validation write-up
  should call out explicitly, not bury.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

MOODYS_ORDER = [
    "Aaa", "Aa1", "Aa2", "Aa3", "A1", "A2", "A3", "Baa1", "Baa2", "Baa3",
    "Ba1", "Ba2", "Ba3", "B1", "B2", "B3", "Caa1", "Caa2", "Caa3", "Ca", "C",
]

EXCLUDE_COLS = ["Paid Off", "Withdrawn (other)", "n_outstanding"]


def load_matrix(csv_path, rating_order=MOODYS_ORDER):
    """Loads a benchmark CSV and returns a square, renormalized transition
    matrix (numpy array) over {rating_order..., 'Default'}, plus the state
    labels in matrix order."""
    df = pd.read_csv(csv_path).set_index("starting_rating")

    states = [r for r in rating_order if r in df.index] + ["Default"]
    n = len(states)
    M = np.zeros((n, n))

    for i, start in enumerate(states):
        if start == "Default":
            M[i, i] = 1.0  # absorbing state
            continue
        row = df.loc[start]
        # keep only rating-to-rating + Default columns, drop PaidOff/Withdrawn
        keep_cols = [c for c in rating_order if c in df.columns] + ["Default"]
        vals = row[keep_cols].astype(float).values
        total = vals.sum()
        if total > 0:
            vals = vals / total * 100  # renormalize to 100% over kept states
        for j, target in enumerate(states):
            if target == "Default":
                M[i, j] = vals[-1] / 100
            else:
                idx = keep_cols.index(target)
                M[i, j] = vals[idx] / 100

    return M, states


def matrix_to_df(M, states):
    return pd.DataFrame(M * 100, index=states, columns=states).round(2)


def plot_comparison(predicted_df, actual_df, title, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(20, 9))
    for ax, df, subtitle in zip(
        axes, [predicted_df, actual_df], ["Predicted (1yr matrix)^3", "Actual published 3-year"]
    ):
        im = ax.imshow(df.values, cmap="Blues", vmin=0, vmax=100)
        ax.set_xticks(range(len(df.columns)))
        ax.set_xticklabels(df.columns, rotation=90, fontsize=7)
        ax.set_yticks(range(len(df.index)))
        ax.set_yticklabels(df.index, fontsize=7)
        ax.set_title(subtitle, fontsize=11)
        # only annotate diagonal + nonzero-ish cells to keep it readable
        for i in range(len(df.index)):
            for j in range(len(df.columns)):
                v = df.values[i, j]
                if v > 3:
                    ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=6,
                            color="white" if v > 50 else "black")
    fig.suptitle(title, fontsize=13)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved {out_path}")


if __name__ == "__main__":
    # --- Moody's: build 1yr matrix, cube it, compare to published 3yr ---
    M1, states = load_matrix("data/moodys_corporate_1y.csv")
    M3_predicted = np.linalg.matrix_power(M1, 3)

    predicted_df = matrix_to_df(M3_predicted, states)
    predicted_df.to_csv("outputs/moodys_predicted_3y_from_1y_cubed.csv")

    # Load actual published 3-year matrix for comparison (same renormalization)
    M3_actual, states_actual = load_matrix("data/moodys_corporate_3y.csv")
    actual_df = matrix_to_df(M3_actual, states_actual)
    actual_df.to_csv("outputs/moodys_actual_3y_renormalized.csv")

    # Difference table
    diff_df = (predicted_df - actual_df).round(2)
    diff_df.to_csv("outputs/moodys_1y3_vs_actual_3y_diff.csv")

    print("\n=== Diagonal comparison (stay-same-rating probability) ===")
    diag_compare = pd.DataFrame({
        "predicted_1y_cubed": np.diag(predicted_df.values),
        "actual_3y": np.diag(actual_df.values),
    }, index=states)
    diag_compare["abs_diff"] = (diag_compare["predicted_1y_cubed"] - diag_compare["actual_3y"]).abs()
    print(diag_compare.round(1))
    diag_compare.to_csv("outputs/moodys_diagonal_comparison.csv")

    plot_comparison(
        predicted_df, actual_df,
        "Moody's Corporate Issuers: (1-Year Matrix)^3 vs. Actual Published 3-Year Matrix",
        "outputs/moodys_1y_cubed_vs_3y_actual.png",
    )

    print(f"\nMean absolute difference across all cells: {diff_df.abs().values.mean():.2f} percentage points")
    print(f"Max absolute difference: {diff_df.abs().values.max():.2f} percentage points")
