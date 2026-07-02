import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

import json
import hashlib
from receipt_parser import parse_receipt

sys.stdout.reconfigure(encoding='utf-8')

# Helper to compute SHA256 hash
def compute_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

with open('data/ocr_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

# Test 1: Chen Feng Ju/014.png (Bank receipt)
h_014 = compute_hash('영수증 보관소/2026-05/Chen Feng Ju/014.png')
ocr_014 = cache.get(h_014, {}).get('raw_text', '')
res_014 = parse_receipt(ocr_014)
print("014.png (Bank receipt) parse result:")
print(f"Type: {res_014.get('type')}")
print(f"Amount: {res_014.get('amount')}")
print(f"Fee: {res_014.get('fee_amount')}")
print(f"Date: {res_014.get('date')}")
print("-" * 50)

# Test 2: Chen Feng Ju/001.png (Gasoline receipt)
h_001 = compute_hash('영수증 보관소/2026-05/Chen Feng Ju/001.png')
ocr_001 = cache.get(h_001, {}).get('raw_text', '')
res_001 = parse_receipt(ocr_001)
print("001.png (Gasoline receipt) parse result:")
print(f"Type: {res_001.get('type')}")
print(f"Amount: {res_001.get('amount')}")
print(f"Date: {res_001.get('date')}")
print(f"Desc: {res_001.get('description')}")
print("-" * 50)
