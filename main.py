from fastapi import FastAPI
app = FastAPI()

@app.get("/welcome")  ## means anyone will wright my url/welcome run the below function
def welcome(): # as usual this funciton could be called from inside the code
    # but I want to call it from  API using app variable
    return {
        "message":"Hello World!"
    }