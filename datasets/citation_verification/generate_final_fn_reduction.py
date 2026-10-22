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
    
    # We want to plot FN (False Negatives)
    configs = df["configuration"].tolist()
    fns = df["fn"].tolist()
    
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
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(configs))
    
    # Custom colors for a professional look - highlight the reduction
    colors = ['#d62728', '#1f77b4', '#ff7f0e', '#2ca02c']
    
    bars = ax.bar(x, fns, width=0.5, color=colors, edgecolor='black', linewidth=0.5)
    
    # Add numerical labels on top of bars
    for rect in bars:
        height = rect.get_height()
        ax.annotate(f'{int(height)}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
            
    # Set y-axis limit
    ax.set_ylim(0, max(fns) + 20)  # Leave room for labels
    
    # Format axes
    ax.set_ylabel('False Negatives')
    ax.set_title('False-Negative Reduction Through Targeted Fixes')
    ax.set_xticks(x)
    ax.set_xticklabels(configs, rotation=15, ha='right')
    
    # Clean up grid and spines
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    output_path = os.path.join(out_dir, "final_false_negative_reduction.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Graph saved to {output_path}")

if __name__ == "__main__":
    main()
