from fastapi import APIRouter, Request, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List
import os
import tempfile
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb import PersistentClient


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
client = PersistentClient(path="./vectordb")
collection = client.get_or_create_collection(name="my_collection")

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
    # Validate file extension for .txt and .pdf
    if not (file.filename.lower().endswith(".txt") or file.filename.lower().endswith(".pdf")):
        error = f"Invalid file: {file.filename}. Only .txt and .pdf files are allowed."
        file_job.append({"filename": file.filename, "error": error})
        return

    try:
        # Save uploaded file to a temporary directory
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Choose loader based on file type
        if file.filename.lower().endswith(".txt"):
            loader = TextLoader(file_path)
        else:
            loader = PyPDFLoader(file_path)

        # Load and chunk the document
        documents = loader.load()
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(documents)
        
        collection.add()
        
        
        
    except Exception as e:
        file_job.append({"filename": file.filename, "error": str(e)})
