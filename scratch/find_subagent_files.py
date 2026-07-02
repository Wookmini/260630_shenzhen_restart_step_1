import os

brain_dir = r"C:\Users\20000177\.gemini\antigravity\brain\a9923e8e-cf15-415c-81e7-2cd999fdb2d4"
print("Brain dir files:")
for root, dirs, files in os.walk(brain_dir):
    for f in files:
        if "report" in f.lower() or "result" in f.lower() or f.endswith(".json") or f.endswith(".txt"):
            p = os.path.join(root, f)
            print(p, os.path.getsize(p))
