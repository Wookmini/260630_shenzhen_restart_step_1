import shutil
import os

dst_dir = r"C:\Users\20000177\.gemini\antigravity\brain\a9923e8e-cf15-415c-81e7-2cd999fdb2d4\browser"
os.makedirs(dst_dir, exist_ok=True)

for fn in ["010.png", "011.png", "012.png"]:
    src = os.path.join("영수증 보관소/2026-05/Chen Feng Ju", fn)
    dst = os.path.join(dst_dir, fn)
    shutil.copy(src, dst)
    print("Copied:", fn)
