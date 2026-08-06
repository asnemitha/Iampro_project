from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parents[3]

DATASET = (
    BASE_DIR
    / "datasets"
    / "prompt_injection"
    / "final"
    / "citeguard_dataset.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "datasets"
    / "prompt_injection"
    / "processed"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load dataset
df = pd.read_csv(DATASET)

# Keep only required columns
df = df[["prompt", "label"]]

# Remove missing values
df = df.dropna()

# Remove duplicate prompts
df = df.drop_duplicates(subset=["prompt"])

# Clean whitespace
df["prompt"] = df["prompt"].astype(str).str.strip()

# Convert labels to integer
df["label"] = df["label"].astype(int)

# Train (80%) / Temp (20%)
train_df, temp_df = train_test_split(
    df,
    test_size=0.20,
    random_state=42,
    stratify=df["label"]
)

# Validation (10%) / Test (10%)
val_df, test_df = train_test_split(
    temp_df,
    test_size=0.50,
    random_state=42,
    stratify=temp_df["label"]
)

# Save files
train_df.to_csv(OUTPUT_DIR / "train.csv", index=False)
val_df.to_csv(OUTPUT_DIR / "validation.csv", index=False)
test_df.to_csv(OUTPUT_DIR / "test.csv", index=False)

print("=" * 50)
print("Training Data Prepared")
print("=" * 50)
print(f"Train:      {len(train_df)}")
print(f"Validation: {len(val_df)}")
print(f"Test:       {len(test_df)}")
print(f"Total:      {len(df)}")