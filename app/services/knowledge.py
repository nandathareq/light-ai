from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import tempfile
import uuid
from fastapi import UploadFile

from ..models.file.file_operations import create_file, FileCreate, get_files
from sqlalchemy.orm import Session
from enum import Enum
from ..models.vector_store import collection

class Status(Enum):
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"
    
def get_files_status(db:Session):
    return map(lambda file : {"filename":file.filename,"error":file.message},get_files(db=db))

async def process_file(file: UploadFile, db: Session):
    if not (file.filename.lower().endswith(".txt") or file.filename.lower().endswith(".pdf")):
        create_file(db, FileCreate(filename=file.filename, 
                                   status=Status.FAILED, 
                                   message=f"Invalid file: {file.filename}. Only .txt and .pdf files are allowed."))
        return

    try:
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        if file.filename.lower().endswith(".txt"):
            loader = TextLoader(file_path)
        else:
            loader = PyPDFLoader(file_path)
            
        documents = loader.load()
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)
        chunks = splitter.split_documents(documents)
        ids = [str(uuid.uuid4()) for i in range(len(chunks))]
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        collection.add(ids=ids, metadatas=metadatas, documents=texts)
        
        create_file(db, FileCreate(filename=file.filename, 
                                   status=Status.COMPLETE))

    except Exception as e:
        create_file(db, FileCreate(filename=file.filename, 
                                   status=Status.FAILED, 
                                   message=str(e)))