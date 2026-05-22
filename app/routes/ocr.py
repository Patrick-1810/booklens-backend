from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import cv2
import numpy as np
import time
from app.core.processor import executar_pipeline_ocr

from app.database.config import get_db
from app.database import models

router = APIRouter(prefix="/ocr", tags=["Reconhecimento"])


@router.post("/extrair-texto")
async def extrair_texto(file: UploadFile = File(...), db: Session = Depends(get_db)):
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

        novo_trecho = models.TrechoLivro(
            nome_arquivo=file.filename,
            texto_extraido=texto_final,
            titulo_livro="Trecho Escaneado pelo BookLens"
        )

        db.add(novo_trecho)
        db.commit()
        db.refresh(novo_trecho)

        return {
            "sucesso": True,
            "id_registro": novo_trecho.id,
            "arquivo": novo_trecho.nome_arquivo,
            "tempo_processamento_segundos": tempo_total,
            "texto_extraido": novo_trecho.texto_extraido,
            "salvo_em": novo_trecho.criado_em.strftime("%d/%m/%Y %H:%M:%S")
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro no processamento do OCR ou na persistência: {str(e)}")