import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('영수증 보관소/2026-05/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

branch_receipts = [r for r in data if r.get('person') == '심천지사']
print(f"Total receipts for 심천지사: {len(branch_receipts)}")
for r in branch_receipts:
    print(f"File: {r.get('file_path')} | Type: {r.get('type')} | Amt: {r.get('amount')} | Desc: {r.get('description')}")
