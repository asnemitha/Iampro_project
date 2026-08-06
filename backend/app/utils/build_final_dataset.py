from datasets import load_from_disk
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[3]

# Public dataset
PUBLIC_DATASET = (
    BASE_DIR
    / "datasets"
    / "prompt_injection"
    / "external"
    / "public_dataset"
)

# Our generated citation prompts
CITATION_DATASET = (
    BASE_DIR
    / "datasets"
    / "prompt_injection"
    / "raw"
    / "citation_prompts.csv"
)

# Output
OUTPUT_DIR = (
    BASE_DIR
    / "datasets"
    / "prompt_injection"
    / "final"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load public dataset
dataset = load_from_disk(str(PUBLIC_DATASET))
public_df = dataset["train"].to_pandas()

# Keep only useful columns
public_df = public_df[["text", "label"]]
public_df.columns = ["prompt", "label"]

public_df["attack_type"] = "Public"
public_df["source"] = "Neuralchemy"

# Load our dataset
citation_df = pd.read_csv(CITATION_DATASET)

# Keep same columns
citation_df = citation_df[
    ["prompt", "label", "attack_type", "source"]
]

# Merge
final_df = pd.concat(
    [public_df, citation_df],
    ignore_index=True
)

# Remove duplicates
final_df.drop_duplicates(
    subset=["prompt"],
    inplace=True
)

# Shuffle
final_df = final_df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

# Save
output_file = OUTPUT_DIR / "citeguard_dataset.csv"

final_df.to_csv(
    output_file,
    index=False
)

print("=" * 50)
print("Final Dataset Created Successfully")
print("=" * 50)
print(final_df.head())
print()
print("Total Samples:", len(final_df))
print("Saved to:", output_file)