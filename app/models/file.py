from sqlalchemy import Column, Integer, String
from .database import Base
from pydantic import BaseModel
from sqlalchemy.orm import Session,relationship

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, nullable=False)
    message = Column(String, nullable=True)
    
    chunks = relationship("Chunk", back_populates="file")
    
class FileCreate(BaseModel):
    filename: str
    status: str
    message: str | None = None

class FileUpdate(BaseModel):
    status: str
    message: str | None = None

class FileOut(BaseModel):
    id: int
    filename: str
    status: str
    message: str | None

class Config:
    orm_mode = True
    
def create_file(db: Session, file: FileCreate):
    db_file = File(**file.model_dump())
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_files(db: Session, skip: int = 0, limit: int = 100):
    return db.query(File).offset(skip).limit(limit).all()

def update_file(db: Session, file_id: int, update: FileUpdate):
    db_file = db.query(File).filter(File.id == file_id).first()
    if db_file:
        for key, value in update.model_dump(exclude_unset=True).items():
            setattr(db_file, key, value)
        db.commit()
        db.refresh(db_file)
    return db_file

def delete_file(db: Session, file_id: int):
    db_file = db.query(File).filter(File.id == file_id).first()
    if db_file:
        db.delete(db_file)
        db.commit()
    return db_file