from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bazi_calculator import generate_summary

# Create FastAPI app (custom name)
bazi_api = FastAPI(
    title="Bazi Analysis API",
    description="API for Bazi / Four Pillars of Destiny analysis",
    version="1.0.0"
)

# Allow all origins (for now)
bazi_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BaziInput(BaseModel):
    birth: str
    time: str
    tz: str
    gender: str

# Use bazi_api instead of app
@bazi_api.post("/bazi")
def bazi_analysis(input_data: BaziInput):
    result = generate_summary(input_data.dict())
    return result

@bazi_api.get("/")
def read_root():
    return {"message": "Welcome to Bazi API! POST to /bazi with birth, time, tz, gender"}



