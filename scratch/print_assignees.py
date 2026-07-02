import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('영수증 보관소/2026-05/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

assignees = set(r.get('assignee') for r in data)
print("Assignees in data.json:", assignees)

# Let's print all records for one assignee, e.g. Chen Feng Ju if it's there
chen_receipts = [r for r in data if r.get('assignee') == 'Chen Feng Ju']
print(f"Total receipts for Chen Feng Ju: {len(chen_receipts)}")
if len(chen_receipts) > 0:
    for r in chen_receipts[:5]:
        print(r)
