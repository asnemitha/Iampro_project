from datasets import load_from_disk
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DATASET_PATH = BASE_DIR / "datasets" / "prompt_injection" / "external" / "public_dataset"

dataset = load_from_disk(str(DATASET_PATH))

print(dataset)
print("\nTrain Sample:")
print(dataset["train"][0])