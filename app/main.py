from fastapi import FastAPI
from routers import controller
from models.database import engine, Base
from models import file

app = FastAPI()

# Create table(s)
Base.metadata.create_all(bind=engine)

# Include the hello router
app.include_router(controller.router)