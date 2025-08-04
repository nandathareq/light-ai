from fastapi import APIRouter, Form, Request, status, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List
from app.models.database import get_db
from ..services.knowledge import get_files_status, process_file
from ..models.vector_store import collection
from sqlalchemy.orm import Session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

information = []

@router.get("/knowledge", response_class=HTMLResponse)
async def show_knowledge_page(request: Request, db: Session = Depends(get_db)):
    
    return templates.TemplateResponse("knowledge.html", {
        "request": request,
        "jobs": get_files_status(db),
        "informations": information
    })

@router.post("/query")
async def query_information(query: str = Form(...)):
    global information
    result = collection.query(
        query_texts=[query],
        n_results=5
    )
    if result['documents']:
        information = result['documents'][0]
    else:
        information = ["No results found."]
    return RedirectResponse(url="/knowledge", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    for file in files:   
        await process_file(file, db)
    return RedirectResponse(url="/knowledge", status_code=status.HTTP_303_SEE_OTHER)