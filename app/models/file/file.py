from sqlalchemy import Column, Integer, String
from ..database import Base
from pydantic import BaseModel

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, nullable=False)
    message = Column(String, nullable=True)
    
class FileCreate(BaseModel):
    filename: str
    status: str
    message: str = None

class FileUpdate(BaseModel):
    status: str
    message: str = None

class FileOut(BaseModel):
    id: int
    filename: str
    status: str
    message: str | None

    class Config:
        orm_mode = True