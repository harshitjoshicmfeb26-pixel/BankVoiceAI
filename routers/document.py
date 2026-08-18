import base64
from fastapi import APIRouter, HTTPException, Form, Response

router = APIRouter()

@router.post("/api/download-pdf")
async def download_pdf(data: str = Form(...), filename: str = Form(...)):
    try:
        pdf_bytes = base64.b64decode(data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid PDF data: {str(e)}")
