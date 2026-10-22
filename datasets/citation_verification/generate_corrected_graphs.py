import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

def main():
    out_dir = "c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification"
    csv_path = os.path.join(out_dir, "final_results_corrected.csv")
    
    df = pd.read_csv(csv_path)
    
    configs = df["configuration"].tolist()
    
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
        row = df[df["configuration"] == config_name].iloc[0]
        tp = int(row["tp"])
        tn = int(row["tn"])
        fp = int(row["fp"])
        fn = int(row["fn"])
        
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
        # As requested: Y-axis: Hallucinated (1), Valid (0). X-axis: Hallucinated (1), Valid (0)
        ax.set_xticklabels(['Hallucinated (1)', 'Valid (0)'])
        ax.set_yticklabels(['Hallucinated (1)', 'Valid (0)'], rotation=0)

    plt.suptitle("Confusion Matrices of Targeted CiteGuard Configurations", fontsize=18, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "final_confusion_matrices.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Reduction in Missed Hallucinations (FN)
    fig, ax = plt.subplots(figsize=(10, 6))
    fns = df["fn"].values
    x = np.arange(len(configs))
    bars = ax.bar(x, fns, width=0.5, color=['#d62728', '#1f77b4', '#ff7f0e', '#2ca02c'], edgecolor='black', linewidth=0.5)
    for rect in bars:
        height = rect.get_height()
        ax.annotate(f'{int(height)}', xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=14, fontweight='bold')
    ax.set_ylim(0, max(fns) + 20)
    ax.set_ylabel('Missed Hallucinations (FN)')
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
    metrics = ["accuracy", "precision", "recall", "f1"]
    metric_labels = ["Accuracy", "Precision", "Recall", "F1 Score"]
    fig, ax = plt.subplots(figsize=(12, 7))
    width = 0.2
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    for i, metric in enumerate(metrics):
        values = df[metric].values
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
    f1_h = df["f1"].values
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

    print("All 4 corrected graphs successfully generated.")

if __name__ == "__main__":
    main()
