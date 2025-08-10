from fastapi import APIRouter, Form, Request, status, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List
from models.database import get_db
from services.knowledge import get_files_status, process_file,retrieve_knowledge
from sqlalchemy.orm import Session

router = APIRouter()
templates = Jinja2Templates(directory="templates")

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/search", response_class=HTMLResponse)
async def show_search_page(request: Request, input: str = Query(None)):
    if not input:
        return templates.TemplateResponse("search.html", {"request": request, "results": ["please input keyword"]})
    
    return templates.TemplateResponse("search.html", {"request": request, "results": retrieve_knowledge(input)})


@router.get("/knowledge", response_class=HTMLResponse)
async def show_knowledge_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("knowledge.html", {"request":request,"jobs": get_files_status(db)})


@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    for file in files:   
        await process_file(file, db)
    return RedirectResponse(url="/knowledge", status_code=status.HTTP_303_SEE_OTHER)