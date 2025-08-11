from typing import List, Optional
from sqlalchemy import Column, Integer, String, or_, ForeignKey, LargeBinary
from .database import Base
from pydantic import BaseModel
from sqlalchemy.orm import Session, relationship
import struct

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    fileid = Column(Integer, ForeignKey("files.id"), nullable=False)
    text = Column(String, nullable=False)
    vector = Column(LargeBinary, nullable=False)  # NOT nullable now
    file = relationship("File", back_populates="chunks")

    def set_vector(self, vec: List[float]):
        self.vector = struct.pack(f'{len(vec)}f', *vec)

    def get_vector(self) -> List[float]:
        length = len(self.vector) // 4
        return list(struct.unpack(f'{length}f', self.vector))

class ChunkCreate(BaseModel):
    fileid: int
    text: str
    vector: List[float]

def create_chunks(db: Session, files: List[ChunkCreate]) -> List[Chunk]:
    chunks = []
    for file in files:
        chunk = Chunk(
            fileid=file.fileid,
            text=file.text,
        )
        chunk.set_vector(file.vector)
        chunks.append(chunk)
    db.add_all(chunks)
    db.commit()
    for chunk in chunks:
        db.refresh(chunk)
    return chunks

def get_chunks(
    db: Session, 
    skip: int = 0, 
    limit: int = 500, 
    keywords: Optional[List[str]] = None
) -> List[Chunk]:
    query = db.query(Chunk)
    
    if keywords:
        conditions = [Chunk.text.ilike(f"%{kw}%") for kw in keywords]
        query = query.filter(or_(*conditions))
    
    return query.offset(skip).limit(limit).all()
