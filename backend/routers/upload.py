import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from utils.file_parser import parse_file
from utils.db import get_connection
from utils.vector_store import add_to_vector_store

router = APIRouter(prefix="/upload", tags=["Upload"])
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../uploads")

ALLOWED = [".csv", ".xlsx", ".xls", ".pdf", ".txt", ".png", ".jpg", ".jpeg"]

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported.")
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    extracted_text = parse_file(save_path)
    if not extracted_text or len(extracted_text) < 10:
        raise HTTPException(status_code=400, detail="Could not extract text from file.")
    conn = get_connection()
    conn.execute("INSERT INTO logs (log_text, source_file) VALUES (?, ?)", (extracted_text, file.filename))
    conn.commit()
    conn.close()
    add_to_vector_store(extracted_text, file.filename)
    return {
        "status": "success",
        "filename": file.filename,
        "characters_extracted": len(extracted_text),
        "message": "File uploaded successfully."
    }

@router.post("/multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    results = []
    errors = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED:
            errors.append({"filename": file.filename, "error": f"File type {ext} not supported."})
            continue

        try:
            save_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(save_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            extracted_text = parse_file(save_path)

            if not extracted_text or len(extracted_text) < 10:
                errors.append({"filename": file.filename, "error": "Could not extract text."})
                continue

            conn = get_connection()
            conn.execute(
                "INSERT INTO logs (log_text, source_file) VALUES (?, ?)",
                (extracted_text, file.filename)
            )
            conn.commit()
            conn.close()

            add_to_vector_store(extracted_text, file.filename)

            results.append({
                "filename": file.filename,
                "status": "success",
                "characters_extracted": len(extracted_text)
            })
            print(f"Uploaded: {file.filename}")

        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})
            print(f"Error uploading {file.filename}: {e}")

    return {
        "status": "done",
        "total_files": len(files),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }

@router.get("/logs")
def get_uploaded_logs():
    conn = get_connection()
    rows = conn.execute("SELECT id, source_file, created_at FROM logs ORDER BY created_at DESC").fetchall()
    conn.close()
    return {"total_logs": len(rows), "logs": [dict(row) for row in rows]}