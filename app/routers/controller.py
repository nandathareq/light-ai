from fastapi import APIRouter, Request, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

file_job = []

@router.get("/knowledge", response_class=HTMLResponse)
async def show_knowledge_page(request: Request):
    return templates.TemplateResponse("knowledge.html", {
        "request": request,
        "jobs": file_job
    })

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    for file in files:
        await process_file(file)

    return RedirectResponse(url="/knowledge", status_code=status.HTTP_303_SEE_OTHER)

async def process_file(file: UploadFile):
    if not file.filename.lower().endswith(".txt"):
        error = f"Invalid file: {file.filename}. Only .txt files are allowed."
        file_job.append({"filename": file.filename, "error": error})
        return
    
    #TODO chunking file
    
    #TODO save into database

    file_job.append({"filename": file.filename, "error": "None"})
