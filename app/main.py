from fastapi import FastAPI
from app.routes import ocr

app = FastAPI(title="BookLens API")

app.include_router(ocr.router)

@app.get("/")
async def root():
    return {"message": "BookLens API está funcionando!"}