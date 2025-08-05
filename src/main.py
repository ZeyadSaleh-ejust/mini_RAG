from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv(".env") # all variables will be initialized inside the system

from routes import base

app = FastAPI()

app.include_router(base.base_router)
