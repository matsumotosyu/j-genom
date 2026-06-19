import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from di.di import calculate_di

app = FastAPI(title="J-Genom DI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class DIRequest(BaseModel):
    text: str
    reading: str


@app.post("/calculate-di")
def calculate(req: DIRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    if not req.reading.strip():
        raise HTTPException(status_code=400, detail="reading is required")
    try:
        result = calculate_di(req.text, req.reading)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
