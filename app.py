"""
SROT — 심천지사 영수증 OCR 변환 웹앱
FastAPI 메인 서버
"""
import os
import sys
import json
import uuid
import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
import fitz  # PyMuPDF

# UTF-8 콘솔 출력
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from ocr_engine import run_ocr, ensure_dirs
from receipt_parser import parse_receipt
from excel_exporter import export_to_excel, get_available_exports

app = FastAPI(title="SROT - 심천지사 영수증 OCR 변환 웹앱")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
RECEIPTS_DB = os.path.join(DATA_DIR, "receipts.json")

# === 데이터 관리 ===

def load_receipts() -> list:
    """영수증 DB 로드"""
    if os.path.exists(RECEIPTS_DB):
        with open(RECEIPTS_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_receipts(receipts: list):
    """영수증 DB 저장"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(RECEIPTS_DB, "w", encoding="utf-8") as f:
        json.dump(receipts, f, ensure_ascii=False, indent=2)


# === 계정과목 및 담당자 마스터 데이터 ===

ACCOUNT_MASTER = [
    {"code": "51131050", "major": "업무추진비", "minor": "일반"},
    {"code": "51061030", "major": "여비교통비", "minor": "해외"},
    {"code": "51201020", "major": "지급임차료", "minor": "사무실임차료"},
    {"code": "51201030", "major": "지급임차료", "minor": "차량임차료"},
    {"code": "51071700", "major": "통신비", "minor": "기타"},
    {"code": "51321010", "major": "해외지사비", "minor": None},
    {"code": "52981010", "major": "(-)잡이익(50)", "minor": "(-)잡이익"},
    {"code": "51031020", "major": "급여(incentive)", "minor": "포상금"},
]

MEMBERS = [
    "신순연", "김명관", "권유석",
    "Zhang Liang", "Lin Jieting", "Lin WeiJian",
    "Piao Mei Ling", "Xiong Feng",
    "Chen Guo Liang", "Liu Ming Liang", "Chen Feng Ju",
]


# === Pydantic 모델 ===

class ReceiptUpdate(BaseModel):
    date: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    person: Optional[str] = None
    account_major: Optional[str] = None
    account_minor: Optional[str] = None
    account_code: Optional[str] = None
    seller: Optional[str] = None
    type: Optional[str] = None


# === API 엔드포인트 ===

@app.post("/api/upload")
async def upload_receipts(files: List[UploadFile] = File(...)):
    """
    영수증 이미지 업로드 (다중 파일)
    업로드 → OCR → 파싱 → DB 저장
    """
    ensure_dirs()
    receipts = load_receipts()
    results = []

    for file in files:
        # 파일 저장
        file_bytes = await file.read()
        ext = os.path.splitext(file.filename or "img.jpg")[1].lower()
        file_id = str(uuid.uuid4())[:8]
        saved_name = f"{file_id}{ext}"
        save_path = os.path.join(UPLOAD_DIR, saved_name)

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        # OCR 실행
        ocr_result = run_ocr(file_bytes, file.filename)
        raw_text = ocr_result.get("raw_text", "")

        # 파싱
        parsed = parse_receipt(raw_text)

        # 영수증 레코드 생성
        receipt = {
            "id": file_id,
            "original_filename": file.filename,
            "saved_filename": saved_name,
            "uploaded_at": datetime.datetime.now().isoformat(),
            "raw_text": raw_text,
            "ocr_hash": ocr_result.get("hash", ""),
            # 파싱 결과
            "type": parsed.get("type", "기타"),
            "date": parsed.get("date"),
            "amount": parsed.get("amount"),
            "currency": parsed.get("currency", "CNY"),
            "seller": parsed.get("seller"),
            "description": parsed.get("description"),
            "account_major": parsed.get("account_major"),
            "account_minor": parsed.get("account_minor"),
            "account_code": parsed.get("account_code"),
            # 사용자 입력 필드
            "person": None,
            "evidence_no": None,
        }

        receipts.append(receipt)
        results.append(receipt)

    save_receipts(receipts)

    return {
        "status": "success",
        "uploaded": len(results),
        "receipts": results
    }


@app.get("/api/receipts")
def get_receipts():
    """전체 영수증 목록 조회"""
    return load_receipts()


@app.get("/api/receipts/{receipt_id}")
def get_receipt(receipt_id: str):
    """개별 영수증 상세 조회"""
    receipts = load_receipts()
    for r in receipts:
        if r["id"] == receipt_id:
            return r
    raise HTTPException(status_code=404, detail="영수증을 찾을 수 없습니다.")


@app.put("/api/receipts/{receipt_id}")
def update_receipt(receipt_id: str, update: ReceiptUpdate):
    """영수증 데이터 수정"""
    receipts = load_receipts()
    for r in receipts:
        if r["id"] == receipt_id:
            update_data = update.model_dump(exclude_none=True)
            r.update(update_data)
            save_receipts(receipts)
            return {"status": "success", "receipt": r}
    raise HTTPException(status_code=404, detail="영수증을 찾을 수 없습니다.")


@app.delete("/api/receipts/{receipt_id}")
def delete_receipt(receipt_id: str):
    """영수증 삭제"""
    receipts = load_receipts()
    original_len = len(receipts)
    receipts = [r for r in receipts if r["id"] != receipt_id]
    if len(receipts) == original_len:
        raise HTTPException(status_code=404, detail="영수증을 찾을 수 없습니다.")

    # 업로드 파일도 삭제
    for r in load_receipts():
        if r["id"] == receipt_id:
            fpath = os.path.join(UPLOAD_DIR, r.get("saved_filename", ""))
            if os.path.exists(fpath):
                os.remove(fpath)
            break

    save_receipts(receipts)
    return {"status": "success", "message": "삭제 완료"}


@app.get("/api/preview/{receipt_id}")
def preview_receipt(receipt_id: str):
    """영수증 원본 이미지 서빙"""
    receipts = load_receipts()
    for r in receipts:
        if r["id"] == receipt_id:
            fpath = os.path.join(UPLOAD_DIR, r.get("saved_filename", ""))
            if os.path.exists(fpath):
                ext = os.path.splitext(fpath)[1].lower()
                
                # PDF인 경우 첫 페이지를 PNG로 렌더링하여 반환 (img 태그 호환성)
                if ext == ".pdf":
                    try:
                        doc = fitz.open(fpath)
                        page = doc.load_page(0)
                        pix = page.get_pixmap(dpi=150)
                        return Response(content=pix.tobytes("png"), media_type="image/png")
                    except Exception as e:
                        print(f"PDF 렌더링 오류: {e}")
                        pass

                media_map = {
                    ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png", ".gif": "image/gif",
                    ".webp": "image/webp", ".pdf": "application/pdf",
                }
                media_type = media_map.get(ext, "application/octet-stream")
                return FileResponse(fpath, media_type=media_type)
            raise HTTPException(status_code=404, detail="이미지 파일을 찾을 수 없습니다.")
    raise HTTPException(status_code=404, detail="영수증을 찾을 수 없습니다.")


@app.get("/api/accounts")
def get_accounts():
    """계정과목 마스터 데이터 조회"""
    return ACCOUNT_MASTER


@app.get("/api/members")
def get_members():
    """담당자 목록 조회"""
    return MEMBERS


@app.post("/api/export/excel")
def export_excel():
    """현재 영수증 데이터를 관리 양식 엑셀로 내보내기"""
    receipts = load_receipts()
    if not receipts:
        raise HTTPException(status_code=400, detail="내보낼 영수증 데이터가 없습니다.")

    try:
        output_path = export_to_excel(receipts)
        filename = os.path.basename(output_path)
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엑셀 생성 실패: {str(e)}")


@app.get("/api/exports")
def list_exports():
    """생성된 엑셀 파일 목록"""
    return get_available_exports()


# === 정적 파일 서빙 ===
os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
