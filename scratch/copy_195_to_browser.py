import shutil
import os

src = r"영수증 보관소/2026-05/신순연/195.png"
dst_dir = r"C:\Users\20000177\.gemini\antigravity\brain\a9923e8e-cf15-415c-81e7-2cd999fdb2d4\browser"
dst = os.path.join(dst_dir, "195.png")

os.makedirs(dst_dir, exist_ok=True)
shutil.copy(src, dst)
print("Copied successfully to:", dst)
