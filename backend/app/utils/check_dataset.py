from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[3]

DATASET = (
    BASE_DIR
    / "datasets"
    / "prompt_injection"
    / "final"
    / "citeguard_dataset.csv"
)

df = pd.read_csv(DATASET)

print("=" * 60)
print("CITEGUARD DATASET REPORT")
print("=" * 60)

# Dataset size
print(f"\nTotal Samples: {len(df)}")

# Missing values
print("\nMissing Values")
print(df.isnull().sum())

# Duplicate prompts
duplicates = df.duplicated(subset=["prompt"]).sum()
print(f"\nDuplicate Prompts: {duplicates}")

# Label distribution
print("\nLabel Distribution")
print(df["label"].value_counts().sort_index())

# Label percentages
print("\nLabel Percentage")
print((df["label"].value_counts(normalize=True) * 100).round(2))

# Attack types
if "attack_type" in df.columns:
    print("\nAttack Type Distribution")
    print(df["attack_type"].value_counts())

# Sources
if "source" in df.columns:
    print("\nSource Distribution")
    print(df["source"].value_counts())

# Prompt length statistics
df["length"] = df["prompt"].astype(str).apply(len)

print("\nPrompt Length Statistics")
print(df["length"].describe())

print("\nSample Records")
print(df.sample(5, random_state=42))

print("\n" + "=" * 60)
print("Dataset verification completed successfully.")
print("=" * 60)