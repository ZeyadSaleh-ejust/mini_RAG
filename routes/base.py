from fastapi import FastAPI,APIRouter
import os


base_router = APIRouter(
    prefix = "/zizo_kosaa",
    tags=["api_v1"]
)
# async ==> Execution is non-blocking and concurrent: You can run other tasks while waiting for something (like a network response).
@base_router.get("/")  ## means anyone will wright my url/welcome run the below function
async def welcome(): # as usual this funciton could be called from inside the code
    # but I want to call it from  API using app variable
    app_name = os.getenv('APP_NAME')
    app_version = os.getenv('APP_VERSION')
    return {
        "app_name": app_name,
        "app_version": app_version
    }


