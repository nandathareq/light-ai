from typing import List
from sqlalchemy import Column, Integer, String, or_, ForeignKey
from .database import Base
from pydantic import BaseModel
from sqlalchemy.orm import Session,relationship

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    fileid = Column(Integer, ForeignKey("files.id"), nullable=False)
    text = Column(String, nullable=False)
    file = relationship("File", back_populates="chunks")

class ChunkCreate(BaseModel):
    fileid: str
    text: str

def create_chunks(db: Session, files: List[ChunkCreate]) -> List[Chunk]:
    chunks = [Chunk(**file.model_dump()) for file in files]
    db.add_all(chunks)
    db.commit()
    for chunk in chunks:
        db.refresh(chunk)
    return chunks

def get_chunks(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    keywords: List[str] = None
) -> List[Chunk]:
    query = db.query(Chunk)
    
    if keywords:
        conditions = [Chunk.text.ilike(f"%{kw}%") for kw in keywords]
        query = query.filter(or_(*conditions))
    
    return query.offset(skip).limit(limit).all()