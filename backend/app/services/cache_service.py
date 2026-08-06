import requests_cache
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
CACHE_PATH = BASE_DIR / "experiments" / "api_cache"

# Create a cached session that persists for 30 days
session = requests_cache.CachedSession(
    str(CACHE_PATH),
    backend='sqlite',
    expire_after=2592000 
)