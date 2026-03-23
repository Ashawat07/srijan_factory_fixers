from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from utils.db import init_db
from routers import upload
from routers import machines
import os

load_dotenv()
init_db()

app = FastAPI(title="MaintainIQ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(machines.router)

@app.get("/")
def root():
    return {"status": "MaintainIQ backend running"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "api_key_loaded": bool(os.getenv("OPENAI_API_KEY"))
    }