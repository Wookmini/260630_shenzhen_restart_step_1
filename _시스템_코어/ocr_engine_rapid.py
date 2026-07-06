"""
OCR 엔진 모듈
RapidOCR(ONNX) + 이미지 해시 기반 캐싱
"""
import os
import hashlib
import json
import numpy as np
import cv2
import fitz  # PyMuPDF
from rapidocr_onnxruntime import RapidOCR

# === 경로 설정 ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(BASE_DIR, "data", "ocr_cache.json")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# OCR 엔진 전역 초기화 (1번만 로드)
ocr_engine = RapidOCR()


def ensure_dirs():
    """필수 디렉토리 생성"""
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def load_cache() -> dict:
    """OCR 캐시 로드"""
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    """OCR 캐시 저장"""
    ensure_dirs()
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def compute_image_hash(image_bytes: bytes) -> str:
    """이미지 바이트의 SHA256 해시 계산"""
    return hashlib.sha256(image_bytes).hexdigest()


def run_ocr(image_bytes: bytes, filename: str = "") -> dict:
    """
    이미지 바이트를 받아 OCR 수행
    캐시에 해시가 존재하면 캐시 결과 반환
    """
    ensure_dirs()
    img_hash = compute_image_hash(image_bytes)

    # 캐시 확인
    cache = load_cache()
    if img_hash in cache:
        return cache[img_hash]

    # PDF인 경우 첫 페이지를 이미지로 변환
    if image_bytes.startswith(b'%PDF-') or filename.lower().endswith('.pdf'):
        try:
            doc = fitz.open(stream=image_bytes, filetype="pdf")
            page = doc.load_page(0)
            pix = page.get_pixmap(dpi=200)
            proc_bytes = pix.tobytes("png")
        except Exception as e:
            return {"error": f"PDF 파싱 실패: {str(e)}", "raw_text": ""}
    else:
        proc_bytes = image_bytes

    # numpy 배열로 변환
    nparr = np.frombuffer(proc_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return {"error": "이미지를 디코딩할 수 없습니다. (지원되지 않는 형식)", "raw_text": ""}

    # 해상도가 너무 큰 경우에만 다운스케일링 (RapidOCR도 너무 크면 메모리를 많이 사용함)
    h, w = img.shape[:2]
    if max(h, w) > 2500:
        scale = 2500 / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    # RapidOCR 실행
    try:
        result, _ = ocr_engine(img)
        raw_text = ""
        if result:
            # result 구조: [[[[x,y], [x,y], [x,y], [x,y]], text, confidence], ...]
            # 줄바꿈으로 연결
            raw_text = "\n".join([item[1] for item in result])
    except Exception as e:
        return {"error": f"OCR 실행 실패: {str(e)}", "raw_text": ""}

    out_result = {
        "hash": img_hash,
        "filename": filename,
        "raw_text": raw_text,
    }

    # 캐시 저장
    cache[img_hash] = out_result
    save_cache(cache)

    return out_result


def run_ocr_from_file(filepath: str) -> dict:
    """파일 경로에서 OCR 수행"""
    with open(filepath, "rb") as f:
        image_bytes = f.read()
    return run_ocr(image_bytes, os.path.basename(filepath))
