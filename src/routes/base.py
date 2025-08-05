from fastapi import FastAPI,APIRouter, Depends
from helpers.config import get_settings,Settings
import os


base_router = APIRouter(
    prefix = "/api/v1",
    tags=["api_v1"]
)
# async ==> Execution is non-blocking and concurrent: You can run other tasks while waiting for something (like a network response).
@base_router.get("/")  ## means anyone will wright my url/welcome run the below function
async def welcome(app_settings:Settings=Depends(get_settings)): # as usual this funciton could be called from inside the code
    # but I want to call it from  API using app variable
    app_settings = get_settings()
    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION
    return {
        "app_name": app_name,
        "app_version": app_version
    }


