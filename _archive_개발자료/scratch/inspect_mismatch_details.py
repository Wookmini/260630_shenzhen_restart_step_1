import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('영수증 보관소/2026-05/data.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

for target_name in ['Chen Feng Ju', '신순연', '김명관']:
    print(f"\n=================== Name: {target_name} ===================")
    for r in results:
        if r.get('person') == target_name:
            print(f"Ev {r.get('evidence_no')}: {r.get('date')} | {r.get('description')} | Amt: {r.get('amount')} | is_fee: {r.get('is_bank_fee_receipt')} | warn: {r.get('validation_warning')} | path: {r.get('file_path')}")
