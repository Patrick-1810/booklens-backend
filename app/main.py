from fastapi import FastAPI, UploadFile, File
import pytesseract
import cv2
import numpy as np

app = FastAPI()

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

@app.post("/extrair-texto")
async def extrair_texto(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    texto = pytesseract.image_to_string(gray, lang='por')

    return {"texto_extraido": texto}