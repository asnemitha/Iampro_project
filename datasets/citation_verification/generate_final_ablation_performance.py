import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

def main():
    out_dir = "c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification"
    csv_path = os.path.join(out_dir, "targeted_fixes_results.csv")
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} does not exist.")
        return

    df = pd.read_csv(csv_path)
    
    metrics = ["accuracy", "precision", "recall", "f1"]
    metric_labels = ["Accuracy", "Precision", "Recall", "F1 Score"]
    
    # Setup publication quality
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'legend.fontsize': 12,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'font.family': 'sans-serif'
    })
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    x = np.arange(len(df))
    width = 0.2
    
    # Custom colors for a professional look
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    bars = []
    for i, metric in enumerate(metrics):
        # Convert to percentage
        values = df[metric] * 100
        bar = ax.bar(x + i * width, values, width, label=metric_labels[i], color=colors[i], edgecolor='black', linewidth=0.5)
        bars.append(bar)
        
        # Add percentage labels on bars
        for rect in bar:
            height = rect.get_height()
            ax.annotate(f'{height:.1f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, rotation=90)
            
    # Set y-axis to 0-100%
    ax.set_ylim(0, 115)  # Leave room for labels
    
    # Format axes
    ax.set_ylabel('Performance (%)')
    ax.set_title('Ablation Performance of Targeted Verification Fixes')
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(df["configuration"])
    
    # Clean up grid and spines
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Legend
    ax.legend(loc='upper right', frameon=True, shadow=False)
    
    plt.tight_layout()
    
    output_path = os.path.join(out_dir, "final_ablation_performance.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Graph saved to {output_path}")

if __name__ == "__main__":
    main()
