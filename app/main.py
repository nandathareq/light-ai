from fastapi import FastAPI
from routers import controller
from models.database import engine, Base

import subprocess
import time
from fastapi import FastAPI
from contextlib import asynccontextmanager

app = FastAPI()
Base.metadata.create_all(bind=engine)

app.include_router(controller.router)