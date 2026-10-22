import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

def main():
    out_dir = "c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification"
    csv_path = os.path.join(out_dir, "targeted_fixes_results.csv")
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} does not exist.")
        return

    df = pd.read_csv(csv_path)
    
    # Setup publication quality
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 12,
        'axes.titlesize': 14,
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,
        'font.family': 'sans-serif'
    })
    
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes = axes.flatten()
    
    configs = df["configuration"].tolist()
    
    for i, config_name in enumerate(configs):
        row = df[df["configuration"] == config_name].iloc[0]
        tp = int(row["tp"])
        tn = int(row["tn"])
        fp = int(row["fp"])
        fn = int(row["fn"])
        
        # Format as standard confusion matrix:
        # [ TN , FP ]
        # [ FN , TP ]
        # Alternatively (True Label on Y, Predicted Label on X):
        # [ TP (True=1, Pred=1) , FN (True=1, Pred=0) ]
        # [ FP (True=0, Pred=1) , TN (True=0, Pred=0) ]
        
        # Let's use the layout common in scikit-learn (True label y-axis, Pred label x-axis):
        #          Predicted 1 (Valid) | Predicted 0 (Hallucinated)
        # True 1 | TP                  | FN
        # True 0 | FP                  | TN
        
        matrix = np.array([[tp, fn],
                           [fp, tn]])
                           
        labels = np.array([[f'TP\n{tp}', f'FN\n{fn}'],
                           [f'FP\n{fp}', f'TN\n{tn}']])
                           
        ax = axes[i]
        sns.heatmap(matrix, annot=labels, fmt='', cmap="Blues", cbar=False, 
                    ax=ax, linewidths=1, linecolor='black', annot_kws={"size": 14, "weight": "bold"})
                    
        ax.set_title(config_name, pad=15)
        ax.set_xlabel('Predicted Label')
        ax.set_ylabel('True Label')
        ax.set_xticklabels(['Valid (1)', 'Hallucinated (0)'])
        ax.set_yticklabels(['Valid (1)', 'Hallucinated (0)'], rotation=0)

    plt.suptitle("Confusion Matrices of Targeted Fixes", fontsize=16, y=1.02)
    plt.tight_layout()
    
    output_path = os.path.join(out_dir, "final_confusion_matrices.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Graph saved to {output_path}")

if __name__ == "__main__":
    main()
