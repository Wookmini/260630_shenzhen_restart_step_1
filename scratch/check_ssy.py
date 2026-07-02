import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('영수증 보관소/2026-05/data.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

print("Shin Soon Yeon items:")
for r in results:
    if r.get('person') == 'Shin Soon Yeon':
        print(f"Ev {r.get('evidence_no')}: {r.get('date')} | {r.get('description')} | Amt: {r.get('amount')} | is_fee_receipt: {r.get('is_bank_fee_receipt')} | warn: {r.get('validation_warning')}")
