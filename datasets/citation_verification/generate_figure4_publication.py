"""
Generate publication-quality Figure 4 (Confusion Matrices) for IEEE ICDDS 2026.

This script reads ground-truth confusion matrix counts from targeted_fixes_results.csv
and produces publication-ready vector and high-DPI raster outputs:
  - figure4_confusion_matrices.pdf (Vector PDF for LaTeX / IEEEtran)
  - figure4_confusion_matrices.svg (Vector SVG for web / vector presentation)
  - figure4_confusion_matrices_600dpi.png (600-DPI PNG for camera-ready raster)

Design Features:
  - Compact 2x2 grid layout (approx. 6.8 x 5.2 inches, matching IEEE double-column width).
  - Clear subfigure labels (a) to (d).
  - Shared outer axis labels ("True Class" on left, "Predicted Class" on bottom) to minimize visual clutter.
  - Subplot-level tick marks for clear independent matrix readability.
  - Exact semantic alignment: Hallucinated citations = Class 1 (positive); Valid citations = Class 0 (negative).
  - Cell orientation:
      [0, 0]: TP (True=1, Pred=1)   [0, 1]: FN (True=1, Pred=0)
      [1, 0]: FP (True=0, Pred=1)   [1, 1]: TN (True=0, Pred=0)
  - Cell annotations include both raw counts and exact class-conditional percentages:
      Row 0 percentages: TP / 500 (Recall of hallucinations) and FN / 500 (Miss rate)
      Row 1 percentages: FP / 100 (False alarm rate) and TN / 100 (Specificity)
  - Monotonic color scaling (Blues, vmin=0, vmax=500) with strict text contrast thresholding
    guaranteeing high legibility on screen and in grayscale photocopy.
  - IEEE-standard typography (serif/Times New Roman fallback) calibrated to print dimensions.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns


def load_and_verify_data(csv_path: Path) -> pd.DataFrame:
    """Load targeted_fixes_results.csv and verify schema and counts."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Target dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # Verify schema
    required_cols = {"configuration", "total", "tp", "tn", "fp", "fn"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in CSV: {missing}")

    # Expected exact configurations and counts from accepted manuscript
    expected = {
        "Current CiteGuard": {"tp": 403, "fn": 97, "fp": 25, "tn": 75},
        "CiteGuard + Author Fix": {"tp": 461, "fn": 39, "fp": 25, "tn": 75},
        "CiteGuard + Venue Fix": {"tp": 409, "fn": 91, "fp": 25, "tn": 75},
        "CiteGuard + Author + Venue Fix": {"tp": 467, "fn": 33, "fp": 25, "tn": 75},
    }

    for config_name, exp_counts in expected.items():
        matching = df[df["configuration"] == config_name]
        if matching.empty:
            raise ValueError(f"Configuration '{config_name}' not found in CSV.")
        row = matching.iloc[0]

        tp, fn, fp, tn = int(row["tp"]), int(row["fn"]), int(row["fp"]), int(row["tn"])
        exp_tp, exp_fn = exp_counts["tp"], exp_counts["fn"]
        exp_fp, exp_tn = exp_counts["fp"], exp_counts["tn"]

        assert tp == exp_tp, f"Mismatch in TP for {config_name}: {tp} != {exp_tp}"
        assert fn == exp_fn, f"Mismatch in FN for {config_name}: {fn} != {exp_fn}"
        assert fp == exp_fp, f"Mismatch in FP for {config_name}: {fp} != {exp_fp}"
        assert tn == exp_tn, f"Mismatch in TN for {config_name}: {tn} != {exp_tn}"

        assert tp + fn == 500, f"Total positive class != 500 in {config_name}"
        assert fp + tn == 100, f"Total negative class != 100 in {config_name}"
        assert tp + fn + fp + tn == 600, f"Total citations != 600 in {config_name}"

    print("Data verification successful: All schemas and counts match paper specifications.")
    return df


def generate_figure4():
    base_dir = Path(__file__).resolve().parent
    csv_path = base_dir / "targeted_fixes_results.csv"

    df = load_and_verify_data(csv_path)

    configs_meta = [
        {"name": "Current CiteGuard", "label": "(a) Current CiteGuard (Baseline)"},
        {"name": "CiteGuard + Author Fix", "label": "(b) CiteGuard + Author Fix"},
        {"name": "CiteGuard + Venue Fix", "label": "(c) CiteGuard + Venue Fix"},
        {"name": "CiteGuard + Author + Venue Fix", "label": "(d) CiteGuard + Author + Venue Fix (Combined)"},
    ]

    # Matplotlib styling tailored for IEEE publications
    plt.rcParams.update({
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'Nimbus Roman', 'DejaVu Serif', 'Times', 'serif'],
        'mathtext.fontset': 'stix',
        'axes.titlesize': 10.5,
        'axes.titleweight': 'bold',
        'axes.labelsize': 10.0,
        'axes.labelweight': 'bold',
        'xtick.labelsize': 9.0,
        'ytick.labelsize': 9.0,
        'figure.titlesize': 12.0,
        'figure.titleweight': 'bold',
        'pdf.fonttype': 42,
        'ps.fonttype': 42,
    })

    # Dimensions: 6.8 inches width (IEEE double-column span), 5.6 inches height
    fig, axes = plt.subplots(2, 2, figsize=(6.8, 5.6))
    axes_flat = axes.flatten()

    class_names = ["Hallucinated (1)", "Valid (0)"]

    for i, meta in enumerate(configs_meta):
        ax = axes_flat[i]
        config_name = meta["name"]
        subplot_title = meta["label"]

        row = df[df["configuration"] == config_name].iloc[0]
        tp = int(row["tp"])
        fn = int(row["fn"])
        fp = int(row["fp"])
        tn = int(row["tn"])

        # Matrix alignment:
        # Row 0: True = Hallucinated (1) -> [TP, FN]
        # Row 1: True = Valid (0)        -> [FP, TN]
        matrix = np.array([[tp, fn],
                           [fp, tn]])

        # Row-conditional percentages (class recall / class specificity)
        pct_tp = (tp / 500.0) * 100.0
        pct_fn = (fn / 500.0) * 100.0
        pct_fp = (fp / 100.0) * 100.0
        pct_tn = (tn / 100.0) * 100.0

        # Uniform color scaling across all subplots: vmin=0, vmax=500
        # Sequential Blues is monotonically increasing in luminance (excellent grayscale contrast)
        sns.heatmap(
            matrix,
            cmap="Blues",
            vmin=0,
            vmax=500,
            cbar=False,
            linewidths=1.2,
            linecolor="white",
            ax=ax
        )

        # High-contrast custom annotations:
        # For dark cells (val >= 250): pure white text
        # For light cells (val < 250): very dark navy text (#0f172a)
        annotations = [
            (0, 0, f"TP = {tp}\n({pct_tp:.1f}%)", tp),
            (0, 1, f"FN = {fn}\n({pct_fn:.1f}%)", fn),
            (1, 0, f"FP = {fp}\n({pct_fp:.1f}%)", fp),
            (1, 1, f"TN = {tn}\n({pct_tn:.1f}%)", tn),
        ]

        for r, c, text_str, val in annotations:
            text_color = "#FFFFFF" if val >= 250 else "#0F172A"
            ax.text(
                c + 0.5,
                r + 0.5,
                text_str,
                ha="center",
                va="center",
                color=text_color,
                fontsize=9.5,
                fontweight="bold",
                linespacing=1.25
            )

        ax.set_title(subplot_title, pad=7, fontsize=10.5)

        # Explicit tick placement and labels on all subplots for immediate readability
        ax.set_xticks([0.5, 1.5])
        ax.set_yticks([0.5, 1.5])
        ax.set_xticklabels(class_names, fontsize=8.5)
        ax.set_yticklabels(class_names, rotation=0, va="center", fontsize=8.5)
        ax.tick_params(length=3, width=0.8)

        # Outer axis titles to keep layout clean and uncrowded
        # Left column (subplots 0 and 2) gets Y-axis label "True Class"
        if i % 2 == 0:
            ax.set_ylabel("True Class", labelpad=6, fontsize=10.0, fontweight="bold")
        else:
            ax.set_ylabel("")

        # Bottom row (subplots 2 and 3) gets X-axis label "Predicted Class"
        if i >= 2:
            ax.set_xlabel("Predicted Class", labelpad=6, fontsize=10.0, fontweight="bold")
        else:
            ax.set_xlabel("")

    plt.suptitle("Confusion Matrices of Targeted CiteGuard Configurations", y=0.985, fontsize=11.5)

    
    # Subtitle note explaining percentages for complete reviewer clarity
    fig.text(
        0.5,
        0.015,
        "Note: Cell percentages reflect row-normalized class recall/specificity (N=500 hallucinations, N=100 valid citations).",
        ha="center",
        fontsize=8.0,
        style="italic",
        color="#334155"
    )

    plt.tight_layout(rect=[0.02, 0.035, 0.98, 0.96])

    # Output paths
    pdf_path = base_dir / "figure4_confusion_matrices.pdf"
    svg_path = base_dir / "figure4_confusion_matrices.svg"
    png_path = base_dir / "figure4_confusion_matrices_600dpi.png"

    # Save Vector PDF
    plt.savefig(pdf_path, format="pdf", dpi=600, bbox_inches="tight")
    print(f"Saved Vector PDF: {pdf_path}")

    # Save Vector SVG
    plt.savefig(svg_path, format="svg", bbox_inches="tight")
    print(f"Saved Vector SVG: {svg_path}")

    # Save 600-DPI PNG
    plt.savefig(png_path, format="png", dpi=600, bbox_inches="tight")
    print(f"Saved 600-DPI PNG: {png_path}")

    plt.close()
    print("Figure 4 generation completed successfully.")


if __name__ == "__main__":
    generate_figure4()
