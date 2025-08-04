from fastapi import FastAPI
from app.routers import controller
from app.models.database import engine, Base
from app.models.file import file

app = FastAPI()

# Create table(s)
Base.metadata.create_all(bind=engine)

# Include the hello router
app.include_router(controller.router)