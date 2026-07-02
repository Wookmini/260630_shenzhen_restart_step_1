import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

p = r"C:\Users\20000177\.gemini\antigravity\brain\a9923e8e-cf15-415c-81e7-2cd999fdb2d4\.system_generated\logs\overview.txt"
if os.path.exists(p):
    with open(p, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for idx, line in enumerate(lines):
        if "view_cfj_008_009" in line:
            print(f"--- Line {idx} ---")
            for i in range(max(0, idx - 2), min(len(lines), idx + 10)):
                print(f"Line {i}: {lines[i].strip()[:250]}")
else:
    print("No overview.txt")
