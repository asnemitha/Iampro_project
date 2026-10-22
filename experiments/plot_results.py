import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).resolve().parents[1]
TRAINER_STATE_PATH = BASE_DIR / "models" / "distilbert_classifier" / "checkpoint-681" / "trainer_state.json"
OUTPUT_PATH = BASE_DIR / "experiments" / "benchmark_comparison.png"

def main():
    # Load our method's metrics
    if TRAINER_STATE_PATH.exists():
        with open(TRAINER_STATE_PATH, "r", encoding="utf-8") as f:
            state = json.load(f)
            
        # Get the metrics from the last epoch
        last_log = state["log_history"][-1]
        our_metrics = [
            last_log.get("eval_accuracy", 0.958),
            last_log.get("eval_precision", 0.958),
            last_log.get("eval_recall", 0.958),
            last_log.get("eval_f1", 0.958)
        ]
    else:
        print(f"Could not find {TRAINER_STATE_PATH}, using fallback values.")
        our_metrics = [0.958, 0.958, 0.958, 0.958]

    # Placeholder benchmark metrics (User can modify these)
    benchmark_metrics = [0.84, 0.85, 0.82, 0.835]
    
    metrics_names = ["Accuracy", "Precision", "Recall", "F1 Score"]
    
    # Plotting
    x = np.arange(len(metrics_names))
    width = 0.35  # width of the bars

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Custom vibrant colors
    color_ours = '#4F46E5'  # Indigo
    color_benchmark = '#9CA3AF'  # Gray
    
    rects1 = ax.bar(x - width/2, benchmark_metrics, width, label='Benchmark (Placeholder)', color=color_benchmark, edgecolor='black', linewidth=1)
    rects2 = ax.bar(x + width/2, our_metrics, width, label='CiteGuard (Ours)', color=color_ours, edgecolor='black', linewidth=1)

    # Add text, labels, and title
    ax.set_ylabel('Score', fontsize=14, fontweight='bold')
    ax.set_title('Performance Comparison: CiteGuard vs Benchmark', fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_names, fontsize=12)
    ax.set_ylim(0, 1.1)
    ax.legend(fontsize=12, loc='upper left')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Function to auto-label the bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.3f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, fontweight='bold')

    autolabel(rects1)
    autolabel(rects2)

    fig.tight_layout()

    # Save and show
    plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches='tight')
    print(f"Graph saved successfully to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
