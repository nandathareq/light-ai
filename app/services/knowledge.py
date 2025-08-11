from typing import Generator
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader
import os
import tempfile
from fastapi import UploadFile
from models.chunk import ChunkCreate, create_chunks, get_chunks
from models.file import FileUpdate, create_file, FileCreate, get_files, update_file, File
from sqlalchemy.orm import Session
from enum import Enum
from langchain_ollama import OllamaLLM
from langchain_ollama import OllamaEmbeddings
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import NLTKTextSplitter
import nltk
import logging

nltk.download('punkt_tab')
logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

llm = OllamaLLM(model="qwen3:8b")
embedding = OllamaEmbeddings(model="nomic-embed-text")
text_splitter = NLTKTextSplitter(chunk_size=1000)

class Status(Enum):
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"
    
def generate_summary(query : str , documents : list[str]) -> Generator[str, None, None]:
    
    context = "\n\n".join(documents)
    prompt = f"""
            You are a helpful assistant. The user has the query: "{query}"

            Here are the retrieved documents:
            \"\"\"{context}\"\"\"

            Please write a concise, clear summary that answers the query using the provided documents.
            Do not include your reasoning steps or any explanation of how you arrived at the answer.
            answer in user query language
            If the documents do not contain enough information, say so explicitly.
            """
    for chunk in llm.stream(prompt):
        yield chunk
    
def retrieve_knowledge(db:Session, query : str) -> list[str]: 
    logger.info("process request")
    chunks = [chunk.text for chunk in get_chunks(db, keywords=query.split())]
    logger.info("end chunking")

    bm25_retriever = BM25Retriever.from_texts(
        chunks, metadatas=[{"source": 1}] * len(chunks)
    )
    
    bm25_retriever.k = 10
    
    logger.info("end BM25")

    faiss_vectorstore = FAISS.from_texts(
        chunks, embedding, metadatas=[{"source": 2}] * len(chunks)
    )
    
    faiss_retriever = faiss_vectorstore.as_retriever(search_kwargs={"k": 10})
    
    logger.info("end faiss")

    ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, faiss_retriever], weights=[0.5, 0.5]
    )
    
    logger.info("end ensemble")

    docs = ensemble_retriever.invoke(query)

    return [doc.page_content for doc in docs]

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
        
        text_splitter = NLTKTextSplitter(chunk_size=200)
        
        chunks = text_splitter.split_text("\n".join(doc.page_content for doc in documents))

        vectors = embedding.embed_documents(chunks)
        
        chunk_creates = [
        ChunkCreate(fileid=file_upload.id, text=chunk_text, vector=vector)
        for chunk_text, vector in zip(chunks, vectors)
        ]

        create_chunks(db, chunk_creates)
        
        update_file(db, file_upload.id, FileUpdate(status=Status.COMPLETE, message=None))

    except Exception as e:
        update_file(db, file_upload.id, FileUpdate(status=Status.FAILED, message=str(e)))