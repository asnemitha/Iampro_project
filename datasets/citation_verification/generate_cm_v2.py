import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

def main():
    out_dir = "c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification"
    
    configs = [
        "Current CiteGuard",
        "CiteGuard + Author Fix",
        "CiteGuard + Venue Fix",
        "CiteGuard + Author + Venue Fix"
    ]
    
    metrics = {
        "Current CiteGuard": {"tp": 403, "fn": 97, "fp": 25, "tn": 75},
        "CiteGuard + Author Fix": {"tp": 461, "fn": 39, "fp": 25, "tn": 75},
        "CiteGuard + Venue Fix": {"tp": 409, "fn": 91, "fp": 25, "tn": 75},
        "CiteGuard + Author + Venue Fix": {"tp": 467, "fn": 33, "fp": 25, "tn": 75}
    }
    
    # Programmatic check
    for name, data in metrics.items():
        tp, fn, fp, tn = data["tp"], data["fn"], data["fp"], data["tn"]
        assert tp + fn == 500, f"TP+FN != 500 for {name}"
        assert fp + tn == 100, f"FP+TN != 100 for {name}"
        assert tp + fn + fp + tn == 600, f"Total != 600 for {name}"
        
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'legend.fontsize': 12,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'font.family': 'sans-serif'
    })
    
    # 1. Confusion Matrix
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    for i, config_name in enumerate(configs):
        data = metrics[config_name]
        tp, fn, fp, tn = data["tp"], data["fn"], data["fp"], data["tn"]
        
        matrix = np.array([[tp, fn],
                           [fp, tn]])
        labels = np.array([[f'TP={tp}', f'FN={fn}'],
                           [f'FP={fp}', f'TN={tn}']])
                           
        ax = axes[i]
        sns.heatmap(matrix, annot=labels, fmt='', cmap="Blues", cbar=False, 
                    ax=ax, linewidths=1, linecolor='black', annot_kws={"size": 16, "weight": "bold"})
                    
        ax.set_title(config_name, pad=15)
        ax.set_xlabel('Predicted Label')
        ax.set_ylabel('True Label')
        
        # Explicitly set the tick positions to ensure labels show up properly
        ax.set_xticks([0.5, 1.5])
        ax.set_yticks([0.5, 1.5])
        ax.set_xticklabels(['Hallucinated (1)', 'Valid (0)'])
        ax.set_yticklabels(['Hallucinated (1)', 'Valid (0)'], rotation=0)

    plt.suptitle("Confusion Matrices of Targeted CiteGuard Configurations", fontsize=18, y=1.02)
    plt.tight_layout()
    output_file = os.path.join(out_dir, "final_confusion_matrices_v2.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Graph saved to {output_file}")

if __name__ == "__main__":
    main()
