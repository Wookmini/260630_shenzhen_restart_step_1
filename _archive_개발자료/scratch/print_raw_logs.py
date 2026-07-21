import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

p = r"C:\Users\20000177\.gemini\antigravity\brain\a9923e8e-cf15-415c-81e7-2cd999fdb2d4\.system_generated\logs\overview.txt"
if os.path.exists(p):
    with open(p, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print("Total lines in overview.txt:", len(lines))
    for idx in range(max(0, len(lines) - 40), len(lines)):
        print(f"Line {idx}: {lines[idx].strip()[:200]}")
else:
    print("No overview.txt")
