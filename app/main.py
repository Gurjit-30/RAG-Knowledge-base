from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

app = FastAPI(title=os.getenv("APP_NAME", "FastAPI Project"))

@app.get("/")
async def root():
    return {
        "message": "Welcome to the API!",
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }
