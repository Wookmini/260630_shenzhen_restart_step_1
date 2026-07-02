import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\영수증 보관소\2026-05\data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== Zhang Liang 출금일자 ===")
for d in data:
    if d.get('person') == 'Zhang Liang':
        print(f"Ev: {d.get('evidence_no')} | IsFee: {d.get('is_bank_fee_receipt')} | Desc: {d.get('description')} | Date: {d.get('date')} | WDate: {d.get('withdrawal_date')}")
