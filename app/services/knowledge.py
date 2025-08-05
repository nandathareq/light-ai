from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import tempfile
import uuid
from fastapi import UploadFile
from models.file import FileUpdate, create_file, FileCreate, get_files, update_file, File
from sqlalchemy.orm import Session
from enum import Enum
from models.vector_store import collection
from langchain.text_splitter import TokenTextSplitter

class Status(Enum):
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"
    
def retrieve_knowledge(query : str): 
    semantic_result = collection.query(
        query_texts=[query],
        n_results=10
    )
    
    fulltext_result = collection.get(where_document={"$contains": query})
    
    results = []
    if semantic_result.get('documents'):
        results = semantic_result['documents'][0] + fulltext_result['documents']
    else:
        results = ["No results found."]
    return results

def get_files_status(db:Session):
    return map(lambda file : {"filename":file.filename,"error":file.message},get_files(db=db))

async def process_file(file: UploadFile, db: Session):
    if not (file.filename.lower().endswith(".txt") or file.filename.lower().endswith(".pdf")):
        create_file(db, FileCreate(filename=file.filename, 
                                   status=Status.FAILED, 
                                   message=f"Only .txt and .pdf files are allowed."))
        return
    
    file_upload = File()
    
    try:
        file_upload = create_file(db, FileCreate(filename=file.filename, status=Status.PROCESSING))
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        if file.filename.lower().endswith(".txt"):
            loader = TextLoader(file_path)
        else:
            loader = PyPDFLoader(file_path)
            
        documents = loader.load()
        
        splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=100)
        chunks = splitter.split_documents(documents)
        
        ids = [str(uuid.uuid4()) for i in range(len(chunks))]
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        collection.add(ids=ids, metadatas=metadatas, documents=texts)
        
        update_file(db, file_upload.id, FileUpdate(status=Status.COMPLETE, message=None))

    except Exception as e:
        update_file(db, file_upload.id, FileUpdate(status=Status.FAILED, message=str(e)))