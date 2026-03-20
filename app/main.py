import os
import json
from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Cookie
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional

from app.auth import authenticate, validate_session, logout
from app.models import LoginRequest
from app.services.document_parser import parse_document, parse_document_from_path
from app.agents.orchestrator import run_optimization_loop

app = FastAPI(title="Auto-Prompt Optimizer Agent", version="1.0.0")

# In-memory storage for uploaded document text
_document_store: dict[str, str] = {}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_PDF = os.path.join(BASE_DIR, "planeplus-explorer-internationalgroup-samplecontract.pdf")

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


def _get_token(request: Request) -> str:
    """Extract session token from cookie or Authorization header."""
    token = request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token or not validate_session(token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token


@app.get("/")
async def root():
    """Serve the main page."""
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))


@app.post("/api/login")
async def login(req: LoginRequest):
    """Authenticate user and return session token."""
    token = authenticate(req.username, req.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    response = JSONResponse({"success": True, "message": "Login successful"})
    response.set_cookie(key="session_token", value=token, httponly=True, samesite="strict")
    return response


@app.post("/api/logout")
async def logout_endpoint(request: Request):
    """Log out and clear session."""
    token = request.cookies.get("session_token")
    if token:
        logout(token)
    response = JSONResponse({"success": True, "message": "Logged out"})
    response.delete_cookie("session_token")
    return response


@app.post("/api/upload-document")
async def upload_document(request: Request, file: UploadFile = File(...)):
    """Upload and parse a PDF document using Azure Document Intelligence."""
    token = _get_token(request)
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file")

    content = await file.read()
    try:
        text = parse_document(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document parsing failed: {str(e)}")

    _document_store[token] = text
    return {"success": True, "message": f"Document parsed successfully ({len(text)} characters extracted)", "preview": text[:500]}


@app.post("/api/use-sample")
async def use_sample_document(request: Request):
    """Parse the bundled sample Certificate of Insurance PDF."""
    token = _get_token(request)
    if not os.path.exists(SAMPLE_PDF):
        raise HTTPException(status_code=404, detail="Sample document not found")

    try:
        text = parse_document_from_path(SAMPLE_PDF)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document parsing failed: {str(e)}")

    _document_store[token] = text
    return {"success": True, "message": f"Sample document parsed ({len(text)} characters extracted)", "preview": text[:500]}


@app.get("/api/run-optimization")
async def run_optimization(request: Request):
    """Run the optimization loop and stream results via SSE."""
    token = _get_token(request)
    document_text = _document_store.get(token)
    if not document_text:
        raise HTTPException(status_code=400, detail="No document loaded. Please upload or select a sample document first.")

    async def event_stream():
        async for event in run_optimization_loop(document_text, num_cycles=3):
            yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
