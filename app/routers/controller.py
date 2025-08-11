from fastapi import APIRouter, Request, status, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from typing import List
from models.database import get_db
from services.knowledge import get_files_status, process_file,retrieve_knowledge, generate_summary
from sqlalchemy.orm import Session
from cachetools import TTLCache
from uuid import uuid4

router = APIRouter()
templates = Jinja2Templates(directory="templates")

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse

router = APIRouter()

summaryCache = TTLCache(maxsize=100, ttl=60)

@router.get("/summary/{summary_id}")
def get_user(summary_id: str):
    return StreamingResponse(
        generate_summary(summaryCache[summary_id]["query"], summaryCache[summary_id]["documents"]),
        media_type="text/plain"
    )

@router.get("/search", response_class=HTMLResponse)
async def show_search_page(request: Request, input: str = Query(None)):

    if not input:
        return templates.TemplateResponse("search.html", {"request": request, "results": ["please input keyword"]})
    
    documents = retrieve_knowledge(input)
    summary_id = str(uuid4())
    summaryCache[summary_id] = {
        "query":input,
        "documents":documents
    }
    
    return templates.TemplateResponse("search.html", {"request": request, "results": documents, "summary_id":summary_id})

@router.get("/knowledge", response_class=HTMLResponse)
async def show_knowledge_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("knowledge.html", {"request":request,"jobs": get_files_status(db)})

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    for file in files:   
        await process_file(file, db)
    return RedirectResponse(url="/knowledge", status_code=status.HTTP_303_SEE_OTHER)