import pandas as pd
import matplotlib.pyplot as plt
import os
import seaborn as sns

def main():
    out_dir = "c:/Users/A S Nemitha/Desktop/CiteGuard/datasets/citation_verification"
    df = pd.read_csv(os.path.join(out_dir, "targeted_fixes_results.csv"))
    
    # 1. targeted_fixes_performance.png
    metrics = ["accuracy", "precision", "recall", "f1"]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(df))
    width = 0.2
    
    for i, metric in enumerate(metrics):
        ax.bar([pos + i * width for pos in x], df[metric], width, label=metric.capitalize())
        
    ax.set_xticks([pos + width * 1.5 for pos in x])
    ax.set_xticklabels(df["configuration"], rotation=15, ha="right")
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Score")
    ax.set_title("Performance by Configuration")
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "targeted_fixes_performance.png"))
    plt.close()
    
    # 2. targeted_fixes_error_type_f1.png
    import json
    with open(os.path.join(out_dir, "targeted_fixes_summary.json"), "r") as f:
        summary = json.load(f)
        
    per_error = summary["per_error_type"]
    
    data = []
    for config, errors in per_error.items():
        for err_type, metrics in errors.items():
            data.append({
                "Configuration": config,
                "Error Type": err_type,
                "F1 Score": metrics["f1"]
            })
            
    df_err = pd.DataFrame(data)
    
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df_err, x="Error Type", y="F1 Score", hue="Configuration")
    plt.title("F1 Score by Error Type and Configuration")
    plt.ylim(0, 1.0)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "targeted_fixes_error_type_f1.png"))
    plt.close()
    
if __name__ == "__main__":
    main()
