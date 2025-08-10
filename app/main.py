from fastapi import FastAPI
from routers import controller
from models.database import engine, Base

import subprocess
import time
from fastapi import FastAPI
from contextlib import asynccontextmanager

app = FastAPI()

# Create table(s)
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Ollama server in background
    process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait for it to boot up (tweak timing or do a health check)
    time.sleep(2)

    # Ensure model is available
    subprocess.run(["ollama", "pull", "qwen3:8b"], check=False)

    print("✅ Ollama started")
    yield  # Application runs while this context is active

    # On shutdown, terminate Ollama process if needed
    process.terminate()
    print("🛑 Ollama stopped")

# Include the hello router
app.include_router(controller.router)