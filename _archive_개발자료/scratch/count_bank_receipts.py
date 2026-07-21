import json
from collections import defaultdict
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('영수증 보관소/2026-05/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for r in data:
    # Let's count how many bank fee receipts each person has
    pass

groups = defaultdict(list)
for r in data:
    groups[r.get('person')].append(r)

for person, receipts in groups.items():
    bank_fees = [r for r in receipts if r.get('is_bank_fee_receipt')]
    print(f"Person: {person} | Total Receipts: {len(receipts)} | Bank Fee Receipts: {len(bank_fees)}")
