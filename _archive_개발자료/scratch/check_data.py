import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\영수증 보관소\2026-05\data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== 1) 출금일자 이상 확인 ===")
missing_withdrawal_dates = set()
for d in data:
    if d.get("withdrawal_date") is None or d.get("withdrawal_date") == d.get("date"):
        missing_withdrawal_dates.add(d.get("person"))
print(f"출금일자와 증빙일자가 같거나 출금일자가 없는 인원: {missing_withdrawal_dates}")

print("\n=== 2) 중국어 내역 확인 ===")
import re
def contains_chinese(text):
    if not text:
        return False
    return bool(re.search(r'[\u4e00-\u9fff]', text))

for d in data:
    desc = d.get("description", "")
    if contains_chinese(desc):
        print(f"Person: {d.get('person')} | Evidence No: {d.get('evidence_no')} | Description: {desc}")
