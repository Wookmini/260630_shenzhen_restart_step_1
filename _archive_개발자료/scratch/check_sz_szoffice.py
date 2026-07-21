import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('영수증 보관소/2026-05/data.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

print("심천지사 items:")
for r in results:
    if r.get('person') == '심천지사':
        print(f"EvNo {r.get('evidence_no')}: {r.get('date')} | {r.get('description')} | Amount: {r.get('amount')} | is_bank_fee_receipt: {r.get('is_bank_fee_receipt')} | principal_amount: {r.get('principal_amount')} | warning: {r.get('validation_warning')} | path: {r.get('file_path')}")
