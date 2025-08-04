from sqlalchemy.orm import Session
from .file import FileCreate, FileOut, FileUpdate, File

def create_file(db: Session, file: FileCreate):
    db_file = File(**file.dict())
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_files(db: Session, skip: int = 0, limit: int = 100):
    return db.query(File).offset(skip).limit(limit).all()

def update_file(db: Session, file_id: int, update: FileUpdate):
    db_file = db.query(File).filter(File.id == file_id).first()
    if db_file:
        for key, value in update.dict(exclude_unset=True).items():
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