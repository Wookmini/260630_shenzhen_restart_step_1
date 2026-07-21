import json
import hashlib
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Helper to compute SHA256 hash
def compute_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

with open('data/ocr_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

h = compute_hash('영수증 보관소/2026-05/심천지사/219.png')
ocr = cache.get(h, {}).get('raw_text', '')
print("=== File 219.png OCR ===")
print(ocr)
