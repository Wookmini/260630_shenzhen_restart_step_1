import os
from ocr_engine import run_ocr
with open('영수증 보관소/2026-06/Lin Wei Jian/012.png', 'rb') as f:
    res = run_ocr(f.read(), '012.png')
    with open('scratch_ocr_out.txt', 'w', encoding='utf-8') as out_f:
        out_f.write(res['raw_text'])
