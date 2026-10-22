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
        "Current CiteGuard": {"tp": 403, "fn": 97, "fp": 25, "tn": 75, "accuracy": 79.67, "precision": 94.16, "recall": 80.60, "f1": 86.85},
        "CiteGuard + Author Fix": {"tp": 461, "fn": 39, "fp": 25, "tn": 75, "accuracy": 89.33, "precision": 94.86, "recall": 92.20, "f1": 93.51},
        "CiteGuard + Venue Fix": {"tp": 409, "fn": 91, "fp": 25, "tn": 75, "accuracy": 80.67, "precision": 94.24, "recall": 81.80, "f1": 87.58},
        "CiteGuard + Author + Venue Fix": {"tp": 467, "fn": 33, "fp": 25, "tn": 75, "accuracy": 90.33, "precision": 94.92, "recall": 93.40, "f1": 94.15}
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
        
        # [0,0]=TP (True=1, Pred=1), [0,1]=FN (True=1, Pred=0)
        # [1,0]=FP (True=0, Pred=1), [1,1]=TN (True=0, Pred=0)
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
        ax.set_xticklabels(['Hallucinated (1)', 'Valid (0)'])
        ax.set_yticklabels(['Hallucinated (1)', 'Valid (0)'], rotation=0)

    plt.suptitle("Confusion Matrices of Targeted CiteGuard Configurations", fontsize=18, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "final_confusion_matrices.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Reduction in Missed Hallucinations (FN)
    fig, ax = plt.subplots(figsize=(10, 6))
    fns = [metrics[c]["fn"] for c in configs]
    x = np.arange(len(configs))
    bars = ax.bar(x, fns, width=0.5, color=['#d62728', '#1f77b4', '#ff7f0e', '#2ca02c'], edgecolor='black', linewidth=0.5)
    for rect in bars:
        height = rect.get_height()
        ax.annotate(f'{int(height)}', xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=14, fontweight='bold')
    ax.set_ylim(0, max(fns) + 20)
    ax.set_ylabel('Missed Hallucinations (FN)')
    ax.set_xlabel('Hallucinated citations incorrectly accepted as valid', fontsize=11, style='italic')
    ax.set_title('Reduction in Missed Hallucinations Through Targeted Fixes')
    ax.set_xticks(x)
    ax.set_xticklabels(configs, rotation=15, ha='right')
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "final_fn_reduction.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # 3. Overall Performance Ablation Graph
    m_keys = ["accuracy", "precision", "recall", "f1"]
    metric_labels = ["Accuracy", "Precision", "Recall", "F1 Score"]
    fig, ax = plt.subplots(figsize=(12, 7))
    width = 0.2
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    for i, metric in enumerate(m_keys):
        values = [metrics[c][metric] for c in configs]
        bar = ax.bar(x + i * width, values, width, label=metric_labels[i], color=colors[i], edgecolor='black', linewidth=0.5)
        for rect in bar:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, rotation=90)
            
    ax.set_ylim(0, 115)
    ax.set_ylabel('Performance (%)')
    ax.set_title('Ablation Performance of Targeted CiteGuard Fixes')
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(configs)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(loc='upper right', frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "final_ablation_performance.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # 4. Corrected Hallucination F1 Graph
    fig, ax = plt.subplots(figsize=(10, 6))
    f1_h = [metrics[c]["f1"] for c in configs]
    bars = ax.bar(x, f1_h, width=0.5, color='#9467bd', edgecolor='black', linewidth=0.5)
    for rect in bars:
        height = rect.get_height()
        ax.annotate(f'{height:.2f}%', xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=12, fontweight='bold')
    ax.set_ylim(0, 105)
    ax.set_ylabel('F1 Score (%)')
    ax.set_title('Hallucination Detection F1 Across Configurations')
    ax.set_xticks(x)
    ax.set_xticklabels(configs, rotation=15, ha='right')
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "final_hallucination_f1.png"), dpi=300, bbox_inches='tight')
    plt.close()

    print("All 4 fixed graphs successfully generated.")

if __name__ == "__main__":
    main()
