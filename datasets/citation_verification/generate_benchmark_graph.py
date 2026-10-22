import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


# ============================================================
# OUTPUT LOCATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_FILE = (
    BASE_DIR / "citation_verification_benchmark.png"
)


# ============================================================
# ACTUAL EXPERIMENTAL RESULTS
# ============================================================

methods = [
    "DOI-only",
    "Crossref Metadata",
    "CiteGuard"
]

accuracy = [
    0.5000,
    0.9933,
    0.9483
]

precision = [
    1.0000,
    0.9921,
    1.0000
]

recall = [
    0.4000,
    1.0000,
    0.9380
]

f1_score = [
    0.5714,
    0.9960,
    0.9680
]


# ============================================================
# METRICS
# ============================================================

metrics = [
    "Accuracy",
    "Precision",
    "Recall",
    "F1 Score"
]

data = np.array([
    accuracy,
    precision,
    recall,
    f1_score
])


# ============================================================
# CREATE GRAPH
# ============================================================

x = np.arange(len(metrics))

width = 0.25

fig, ax = plt.subplots(
    figsize=(10, 6)
)


# ============================================================
# DRAW BARS
# ============================================================

for i, method in enumerate(methods):

    values = data[:, i]

    bars = ax.bar(
        x + (i - 1) * width,
        values,
        width,
        label=method
    )

    # Value labels
    for bar, value in zip(
        bars,
        values
    ):

        ax.text(
            bar.get_x()
            + bar.get_width() / 2,

            value + 0.015,

            f"{value * 100:.2f}%",

            ha="center",
            va="bottom",

            fontsize=9
        )


# ============================================================
# AXES
# ============================================================

ax.set_xlabel(
    "Evaluation Metrics",
    fontsize=11
)

ax.set_ylabel(
    "Score",
    fontsize=11
)

ax.set_title(
    "Citation Verification Performance Comparison",
    fontsize=13,
    fontweight="bold"
)

ax.set_xticks(x)

ax.set_xticklabels(
    metrics
)


# ============================================================
# Y AXIS
# ============================================================

ax.set_ylim(
    0,
    1.12
)

yticks = np.arange(
    0,
    1.01,
    0.1
)

ax.set_yticks(
    yticks
)

ax.set_yticklabels(
    [
        f"{int(value * 100)}%"
        for value in yticks
    ]
)


# ============================================================
# GRID
# ============================================================

ax.grid(
    axis="y",
    linestyle="--",
    alpha=0.4
)

ax.set_axisbelow(
    True
)


# ============================================================
# LEGEND
# ============================================================

ax.legend(
    loc="lower right"
)


# ============================================================
# FINAL LAYOUT
# ============================================================

plt.tight_layout()


# ============================================================
# SAVE
# ============================================================

plt.savefig(
    OUTPUT_FILE,
    dpi=300,
    bbox_inches="tight"
)


# ============================================================
# DISPLAY
# ============================================================

plt.show()


# ============================================================
# TERMINAL OUTPUT
# ============================================================

print()
print("=" * 60)
print("GRAPH GENERATED SUCCESSFULLY")
print("=" * 60)

print(
    f"Saved to:\n{OUTPUT_FILE}"
)

print(
    "Resolution: 300 DPI"
)

print("=" * 60)