import json
import time
import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

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
        raise HTTPException(status_code=400, detail="Falha ao decodificar a imagem enviada.")

    try:
        resultado_ocr = executar_pipeline_ocr(img)
        tempo_total = round(time.time() - inicio_tempo, 2)

        titulo_identificado = resultado_ocr["titulo"] if resultado_ocr["titulo"] else "Documento sem título"

        novo_documento = models.DocumentoPublico(
            nome_arquivo=file.filename,
            texto_extraido=resultado_ocr["texto_completo_votado"],
            titulo_documento=titulo_identificado,
            elementos_formatados=json.dumps(resultado_ocr["elementos"], ensure_ascii=False)
        )

        db.add(novo_documento)
        db.commit()
        db.refresh(novo_documento)

        return {
            "sucesso": True,
            "id_registro": novo_documento.id,
            "arquivo": novo_documento.nome_arquivo,
            "tempo_processamento_segundos": tempo_total,
            "estrutura": {
                "titulo": titulo_identificado,
                "paragrafos": resultado_ocr["paragrafos"],
                "elementos": resultado_ocr["elementos"],
                "largura_pagina": resultado_ocr["largura_pagina"],
                "altura_pagina": resultado_ocr["altura_pagina"]
            },
            "texto_completo": resultado_ocr["texto_completo_votado"],
            "palavras_suspeitas": resultado_ocr["palavras_suspeitas"],
            "salvo_em": novo_documento.criado_em.strftime("%d/%m/%Y %H:%M:%S")
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro no processamento do OCR/Layout: {str(e)}")