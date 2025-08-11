from fastapi import FastAPI
from routers import controller
from models.database import engine, Base

from fastapi import FastAPI

app = FastAPI()
Base.metadata.create_all(bind=engine)

app.include_router(controller.router)