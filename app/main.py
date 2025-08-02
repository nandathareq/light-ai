from fastapi import FastAPI
from app.routers import controller

app = FastAPI()

# Include the hello router
app.include_router(controller.router)