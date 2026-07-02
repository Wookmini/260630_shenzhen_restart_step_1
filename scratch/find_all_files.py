import os

target_dir = '영수증 보관소/2026-05'
for item in os.listdir(target_dir):
    a_dir = os.path.join(target_dir, item)
    if os.path.isdir(a_dir):
        files = os.listdir(a_dir)
        processed = [f for f in files if f.endswith('.pdf.processed')]
        pngs = [f for f in files if f.endswith('.png')]
        other = [f for f in files if not f.endswith('.pdf.processed') and not f.endswith('.png')]
        print(f"Assignee: {item}")
        print(f"  Processed PDFs: {len(processed)}")
        print(f"  PNGs: {len(pngs)}")
        if other:
            print(f"  Other: {other}")
