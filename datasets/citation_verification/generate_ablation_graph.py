import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Paths
RESULTS_FILE = Path(__file__).resolve().parent / "ablation_results.csv"
DETAILED_FILE = Path(__file__).resolve().parent / "ablation_detailed_results.csv"
PERF_PNG = Path(__file__).resolve().parent / "ablation_performance.png"
ERR_TYPE_PNG = Path(__file__).resolve().parent / "ablation_error_type_f1.png"

def plot_performance():
    df = pd.read_csv(RESULTS_FILE)
    
    # We want to plot Accuracy, Precision, Recall, F1 for the 5 configurations
    # Configurations are expected in the order they appear in the file
    metrics = ["accuracy", "precision", "recall", "f1"]
    
    # Melt dataframe for seaborn barplot
    df_melted = df.melt(id_vars="configuration", value_vars=metrics, var_name="Metric", value_name="Score")
    
    # Capitalize metric names for better labels
    df_melted["Metric"] = df_melted["Metric"].str.capitalize()
    
    # Order of configurations
    config_order = [
        "DOI-only",
        "Crossref Metadata",
        "Crossref + Title",
        "Crossref + Title + Authors + Year + Venue",
        "Full CiteGuard"
    ]
    
    plt.figure(figsize=(14, 8))
    sns.set_theme(style="whitegrid")
    
    ax = sns.barplot(
        data=df_melted, 
        x="configuration", 
        y="Score", 
        hue="Metric",
        order=config_order,
        palette="deep"
    )
    
    plt.title("Ablation Study Performance: Citation Verification", fontsize=16, fontweight='bold', pad=20)
    plt.ylabel("Score", fontsize=14)
    plt.xlabel("Configuration", fontsize=14)
    plt.ylim(0, 1.05)
    plt.xticks(rotation=15, ha='right', fontsize=12)
    plt.legend(title="Metrics", fontsize=12, title_fontsize=12)
    plt.tight_layout()
    plt.savefig(PERF_PNG, dpi=300)
    plt.close()

def plot_error_type_f1():
    df_det = pd.read_csv(DETAILED_FILE)
    
    error_types = df_det["error_type"].unique()
    configs = df_det["configuration"].unique()
    
    records = []
    
    for c in configs:
        for et in error_types:
            sub = df_det[(df_det["configuration"] == c) & (df_det["error_type"] == et)]
            if len(sub) == 0:
                continue
                
            y_true = sub["ground_truth"].tolist()
            y_pred = sub["prediction"].tolist()
            
            tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
            tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
            fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
            fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            records.append({
                "Configuration": c,
                "Error Type": et,
                "F1 Score": f1
            })
            
    df_f1 = pd.DataFrame(records)
    
    config_order = [
        "DOI-only",
        "Crossref Metadata",
        "Crossref + Title",
        "Crossref + Title + Authors + Year + Venue",
        "Full CiteGuard"
    ]
    
    plt.figure(figsize=(14, 8))
    sns.set_theme(style="whitegrid")
    
    sns.barplot(
        data=df_f1,
        x="Error Type",
        y="F1 Score",
        hue="Configuration",
        hue_order=config_order,
        palette="deep"
    )
    
    plt.title("Ablation Study: F1 Score by Error Type", fontsize=16, fontweight='bold', pad=20)
    plt.ylabel("F1 Score", fontsize=14)
    plt.xlabel("Error Type", fontsize=14)
    plt.ylim(0, 1.05)
    plt.xticks(rotation=30, ha='right', fontsize=12)
    plt.legend(title="Configuration", fontsize=10, title_fontsize=11)
    plt.tight_layout()
    plt.savefig(ERR_TYPE_PNG, dpi=300)
    plt.close()

if __name__ == "__main__":
    plot_performance()
    plot_error_type_f1()
    print("Graphs generated successfully.")
