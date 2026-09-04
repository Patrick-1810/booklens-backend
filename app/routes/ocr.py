import time
import cv2
import numpy as np
from typing import List, Optional, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.processor import executar_pipeline_ocr
from app.database.config import get_db
from app.database import models
from app.core.security import obter_usuario_atual

from datetime import datetime
from app.core.docling_processor import executar_docling

router = APIRouter(prefix="/ocr", tags=["Reconhecimento"])


# --- SCHEMAS PYDANTIC ---

class DocumentoUpdate(BaseModel):
    titulo: Optional[str] = None
    elementos: Optional[List[Any]] = None
    paragrafos: Optional[List[str]] = None
    anotacoes: Optional[str] = None


# --- ROTAS DA API ---

@router.post("/extrair-texto")
async def extrair_texto(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario_atual: models.User = Depends(obter_usuario_atual),
):
    """Extrai texto de uma imagem via OCR. Requer autenticação."""
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
        resultado_docling = executar_docling(img)

        tempo_total = round(time.time() - inicio_tempo, 2)

        titulo_extraido = str(resultado_ocr.get("titulo") or "Documento sem título").strip()
        titulo_identificado = titulo_extraido if titulo_extraido else "Documento sem título"

        novo_documento = models.DocumentoPublico(
            nome_arquivo=file.filename,
            texto_extraido=resultado_ocr["texto_completo_votado"],
            titulo_documento=titulo_identificado,
            elementos_formatados=resultado_ocr["elementos"],
            usuario_id=usuario_atual.id,
        )

        db.add(novo_documento)
        db.commit()
        db.refresh(novo_documento)

        data_salvamento = novo_documento.criado_em.strftime(
            "%d/%m/%Y %H:%M:%S") if novo_documento.criado_em else datetime.now().strftime("%d/%m/%Y %H:%M:%S")

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
            "docling": {  
            "texto_markdown": resultado_docling["texto_markdown"],
            "paragrafos": resultado_docling["paragrafos"]
            },
            "texto_completo": resultado_ocr["texto_completo_votado"],
            "palavras_suspeitas": resultado_ocr["palavras_suspeitas"],
            "salvo_em": data_salvamento
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro no processamento do OCR/Layout: {str(e)}")


@router.put("/documentos/{doc_id}")
async def atualizar_documento(
    doc_id: int,
    dados: DocumentoUpdate,
    db: Session = Depends(get_db),
    usuario_atual: models.User = Depends(obter_usuario_atual),
):
    """Atualiza um documento. Requer autenticação e que o documento pertença ao usuário."""
    doc = db.query(models.DocumentoPublico).filter(models.DocumentoPublico.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")

    # Valida que o documento pertence ao usuário autenticado
    if doc.usuario_id is not None and doc.usuario_id != usuario_atual.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para editar este documento."
        )

    try:
        if dados.titulo is not None:
            doc.titulo_documento = dados.titulo

        if dados.elementos is not None:
            doc.elementos_formatados = dados.elementos

        if dados.paragrafos is not None:
            doc.texto_extraido = "\n\n".join(dados.paragrafos)

        if dados.anotacoes is not None:
            doc.anotacoes = dados.anotacoes

        db.commit()
        db.refresh(doc)

        return {
            "sucesso": True,
            "message": "Documento atualizado com sucesso!",
            "id_registro": doc.id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar o documento: {str(e)}")