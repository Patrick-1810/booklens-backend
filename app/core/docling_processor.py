import os

os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["TORCHDYNAMO_DISABLE"] = "1"

import tempfile
import cv2
from docling.document_converter import DocumentConverter


def executar_docling(img_matriz):
    """
    Salva a imagem em disco e executa o Docling desativando
    a compilação dinâmica C++ no Windows.
    """
    tmp_path = None
    try:
        # Cria o arquivo temporário de imagem
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
            cv2.imwrite(tmp_path, img_matriz)

        # Configura o conversor padrão do Docling
        converter = DocumentConverter()

        # Executa a conversão no arquivo de imagem
        result = converter.convert(tmp_path)
        markdown_text = result.document.export_to_markdown()

        paragrafos = [p.strip() for p in markdown_text.split("\n\n") if p.strip()]

        return {
            "texto_markdown": markdown_text,
            "paragrafos": paragrafos
        }
    except Exception as e:
        print(f"[ERRO DOCLING DETALHADO]: {str(e)}")
        return {
            "texto_markdown": f"Falha ao processar via Docling: {str(e)}",
            "paragrafos": []
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass