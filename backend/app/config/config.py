from pathlib import Path

# =========================
# Project Paths
# =========================

BASE_DIR = Path(__file__).resolve().parents[3]

TRAIN_DATA = BASE_DIR / "datasets" / "prompt_injection" / "processed" / "train.csv"
VALIDATION_DATA = BASE_DIR / "datasets" / "prompt_injection" / "processed" / "validation.csv"
TEST_DATA = BASE_DIR / "datasets" / "prompt_injection" / "processed" / "test.csv"

MODEL_OUTPUT_DIR = BASE_DIR / "models" / "distilbert_classifier"

# =========================
# Model
# =========================

MODEL_NAME = "distilbert-base-uncased"
NUM_LABELS = 3

# =========================
# Training
# =========================

MAX_LENGTH = 128
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
EPOCHS = 3
RANDOM_SEED = 42