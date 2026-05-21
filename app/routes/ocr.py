from fastapi import APIRouter, UploadFile, File, HTTPException
import cv2
import numpy as np
import time
from app.core.processor import executar_pipeline_ocr

router = APIRouter(prefix="/ocr", tags=["Reconhecimento"])


@router.post("/extrair-texto")
async def extrair_texto(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="O arquivo enviado precisa ser uma imagem válida.")

    inicio_tempo = time.time()

    contents = await file.read()

    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Falha ao decodificar a imagem enviada")

    try:
        texto_final = executar_pipeline_ocr(img)

        tempo_total = round(time.time() - inicio_tempo, 2)

        return {
            "sucesso": True,
            "arquivo": file.filename,
            "tempo_processamento_segundos": tempo_total,
            "texto_extraido": texto_final
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento do OCR: {str(e)}")