from datasets import load_dataset
from pathlib import Path

dataset = load_dataset("neuralchemy/Prompt-injection-dataset", "core")

BASE_DIR = Path(__file__).resolve().parents[3]
SAVE_PATH = BASE_DIR / "datasets" / "prompt_injection" / "external" / "public_dataset"

dataset.save_to_disk(str(SAVE_PATH))

print("Dataset downloaded successfully!")