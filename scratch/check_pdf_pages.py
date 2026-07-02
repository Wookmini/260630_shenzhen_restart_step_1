import fitz, os

path = '과거 참고데이터/26년 5월/5월 스캔본_재정비/엑셀 대응'
for f in sorted(os.listdir(path)):
    if f.endswith('.pdf'):
        doc = fitz.open(os.path.join(path, f))
        print(f"{f}: {len(doc)} pages")
