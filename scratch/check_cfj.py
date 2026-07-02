import os
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('영수증 보관소/2026-05/data.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

# Get files in folder
folder = '영수증 보관소/2026-05/Chen Feng Ju'
files = sorted(os.listdir(folder))

print("Files in folder Chen Feng Ju:")
for fn in files:
    print(fn)

print("\nData for Chen Feng Ju in data.json:")
for r in results:
    if r.get('person') == 'Chen Feng Ju':
        print(f"Ev {r.get('evidence_no')}: {r.get('date')} | {r.get('description')} | Amt: {r.get('amount')} | file: {os.path.basename(r.get('file_path'))}")
