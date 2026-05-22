from fastapi import FastAPI
from app.routes import ocr
from fastapi.middleware.cors import CORSMiddleware
from app.database import models
from app.database.config import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="BookLens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ocr.router)

@app.get("/")
async def root():
    return {"message": "BookLens API está funcionando!"}