import requests
import json

payload = {"prompt": "how to make a coffee"}
try:
    r = requests.post("http://127.0.0.1:8000/analyze", json=payload)
    print("Status:", r.status_code)
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
