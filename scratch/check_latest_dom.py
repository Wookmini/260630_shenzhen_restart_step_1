import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

folder = r"C:\Users\20000177\.gemini\antigravity\brain\a9923e8e-cf15-415c-81e7-2cd999fdb2d4\.tempmediaStorage"
dom_files = sorted([f for f in os.listdir(folder) if f.startswith("dom_")], reverse=True)

print("Latest 5 DOM files:")
for df in dom_files[:5]:
    p = os.path.join(folder, df)
    print(f"--- File: {df} (size: {os.path.getsize(p)}) ---")
    with open(p, 'r', encoding='utf-8') as f:
        print(f.read()[:500])
