from fastapi import FastAPI
from routers import controller
from models.database import engine, Base

import subprocess
import time
from fastapi import FastAPI
from contextlib import asynccontextmanager

app = FastAPI()
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)

    subprocess.run(["ollama", "pull", "qwen3:8b"], check=False)

    yield  # Application runs while this context is active

    process.terminate()

app.include_router(controller.router)