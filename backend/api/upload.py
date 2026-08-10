from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import pymupdf  # PyMuPDF
import io

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF, extract text from each page,
    and return as a list of document chunks.
    """
    # Validate file type by name and content-type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF (.pdf extension required)")

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Open PDF — catch corrupt/invalid files specifically
    try:
        doc = pymupdf.open(stream=content, filetype="pdf")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not open PDF — file may be corrupted or password-protected: {e}")

    try:
        all_text: List[str] = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                all_text.append(text.strip())
    finally:
        doc.close()

    if not all_text:
        raise HTTPException(
            status_code=400,
            detail="No extractable text found in this PDF. It may be a scanned image-only PDF. Please use a text-based PDF."
        )

    return {
        "documents": all_text,
        "page_count": len(all_text),
        "total_chars": sum(len(t) for t in all_text),
        "filename": file.filename,
    }