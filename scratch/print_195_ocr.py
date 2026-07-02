import json
import os
import sys
import hashlib
sys.stdout.reconfigure(encoding='utf-8')

# Helper to compute SHA256 hash
def compute_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

with open('data/ocr_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

for fn in ["../신순연/195.png"]:
    p = os.path.normpath(os.path.join("영수증 보관소/2026-05/Chen Feng Ju", fn))
    h = compute_hash(p)
    ocr = cache.get(h, {}).get('raw_text', '')
    print(f"=== OCR for {fn} ===")
    print(ocr)
