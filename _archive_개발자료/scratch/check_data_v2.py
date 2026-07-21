import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\영수증 보관소\2026-05\data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== 출금일자 배정 확인 ===")
for d in data:
    person = d.get('person')
    ev = d.get('evidence_no')
    date = d.get('date')
    wdate = d.get('withdrawal_date')
    is_fee = d.get('is_bank_fee_receipt')
    if person == 'Chen Feng Ju' or person == '신순연':
        print(f"{person} | Ev {ev} | IsFee: {is_fee} | Date: {date} | WDate: {wdate}")

