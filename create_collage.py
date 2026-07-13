import fitz
import os
import random
import io
from PIL import Image, ImageChops

def trim_white_space(im):
    # Convert to grayscale to find bounding box of non-white pixels
    gray = im.convert('L')
    # Anything darker than 240 is considered content
    bw = gray.point(lambda x: 0 if x > 240 else 255, '1')
    bbox = bw.getbbox()
    if bbox:
        # Add a small padding
        padding = 10
        left = max(0, bbox[0] - padding)
        top = max(0, bbox[1] - padding)
        right = min(im.width, bbox[2] + padding)
        bottom = min(im.height, bbox[3] + padding)
        return im.crop((left, top, right, bottom))
    return im

dir_path = r'과거 참고\26년 5월\5월 스캔본_재정비\엑셀 대응'
all_files = [f for f in os.listdir(dir_path) if f.endswith('.pdf')]

# Separate by file size: Photos (scans) are usually > 300KB, digital fapiaos are ~70KB
digital_pdfs = []
photo_pdfs = []

for f in all_files:
    size = os.path.getsize(os.path.join(dir_path, f))
    if size > 300 * 1024:
        photo_pdfs.append(f)
    else:
        digital_pdfs.append(f)

random.seed(42)
random.shuffle(digital_pdfs)
random.shuffle(photo_pdfs)

# Create a list where digital PDFs are drawn first, and photo PDFs are drawn last (on top)
# Multiply to get enough density
# User request: Focus heavily on photos rather than digital fapiaos
draw_list = (digital_pdfs[:10] * 2) + (photo_pdfs * 10)

canvas_w = 1920
canvas_h = 1080
bg = Image.new('RGBA', (canvas_w, canvas_h), (6, 9, 15, 255))

for idx, f in enumerate(draw_list):
    try:
        doc = fitz.open(os.path.join(dir_path, f))
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        img_data = pix.tobytes('png')
        img = Image.open(io.BytesIO(img_data)).convert('RGBA')
        
        # Trim white space (A4 empty borders)
        img = trim_white_space(img)
        
        # Scale down even more for a massive pile effect
        img.thumbnail((300, 400), Image.Resampling.LANCZOS)
        
        # Random rotation
        rot = random.randint(-90, 90)
        img_rot = img.rotate(rot, expand=True, fillcolor=(0,0,0,0))
        
        # Random position (expand negative coordinates to fill left side)
        x = random.randint(-400, canvas_w - int(img_rot.width*0.3))
        y = random.randint(-300, canvas_h - int(img_rot.height*0.3))
        
        bg.paste(img_rot, (x, y), img_rot)
        doc.close()
    except Exception as e:
        print(f"Failed on {f}: {e}")

out_path = r'_발표자료\V2\images\receipt_bg.png'
os.makedirs(os.path.dirname(out_path), exist_ok=True)
bg.save(out_path)
print("Collage created at", out_path)
