from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import ocr, auth, dictionary
from app.database.config import Base, engine
from app.database import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="BookLens API")

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ocr.router)
app.include_router(auth.router)
app.include_router(dictionary.router)

@app.get("/")
async def root():
    return {"message": "BookLens API está funcionando!"}