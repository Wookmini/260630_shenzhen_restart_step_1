import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

p = r"C:\Users\20000177\.gemini\antigravity\brain\a9923e8e-cf15-415c-81e7-2cd999fdb2d4\.system_generated\logs\overview.txt"
if os.path.exists(p):
    with open(p, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if "subagent" in line.lower() or "195.png" in line or "37.5" in line:
                print(f"Line {idx}: {line.strip()[:200]}")
else:
    print("No overview.txt")
