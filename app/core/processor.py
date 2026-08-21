import os
import re
import cv2
import numpy as np
import pandas as pd
import pytesseract
from spellchecker import SpellChecker

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

spell = SpellChecker(language='pt')


def deskew_hough_lines(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)

    if lines is None:
        return image

    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if -15 < angle < 15:
            angles.append(angle)

    if not angles:
        return image

    angulo_mediano = np.median(angles)
    if abs(angulo_mediano) > 0.3:
        (h, w) = image.shape[:2]
        centro = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(centro, angulo_mediano, 1.0)
        image = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

    return image


def analisador_lexico_corretor(texto):
    palavras = texto.split()
    texto_corrigido = []

    for palavra in palavras:
        palavra_limpa = ''.join(e for e in palavra if e.isalnum())

        if palavra_limpa and not palavra_limpa.isnumeric():
            if palavra_limpa.lower() not in spell:
                sugestao = spell.correction(palavra_limpa.lower())
                if sugestao:
                    if palavra[0].isupper():
                        sugestao = sugestao.capitalize()
                    palavra = palavra.replace(palavra_limpa, sugestao)

        texto_corrigido.append(palavra)

    return " ".join(texto_corrigido)


def extrair_sugestoes_e_palavras_suspeitas(texto):
    tokens = texto.split()
    suspeitas = []
    regex_ruido = re.compile(r'[€$@%&*#\\/<>_{}\[\]\|]')

    for i, token in enumerate(tokens):
        palavra_limpa = token.strip()
        is_suspeita = False

        if palavra_limpa.endswith('-') and len(palavra_limpa) > 1:
            is_suspeita = True
            if i + 1 < len(tokens):
                proxima = tokens[i + 1].strip('.,;:!?()""\'')
                sugestao_junta = palavra_limpa[:-1] + proxima
                suspeitas.append({"original": palavra_limpa, "sugestoes": [sugestao_junta]})
                continue

        elif regex_ruido.search(palavra_limpa):
            is_suspeita = True

        elif len(palavra_limpa) <= 3 and not palavra_limpa.isalnum() and not palavra_limpa.isnumeric():
            is_suspeita = True

        if is_suspeita:
            termo_original = re.sub(r'^[^\w]+|[^\w]+$', '', palavra_limpa)
            if termo_original:
                suspeitas.append({"original": termo_original, "sugestoes": []})

    vistas = set()
    suspeitas_unicas = []
    for item in suspeitas:
        chave = item["original"].lower()
        if chave and chave not in vistas:
            vistas.add(chave)
            suspeitas_unicas.append(item)

    return suspeitas_unicas


def analisar_layout_morfologico_e_zscore(imagem_cv):
    altura_pagina, largura_pagina = imagem_cv.shape[:2]
    gray = cv2.cvtColor(imagem_cv, cv2.COLOR_BGR2GRAY)

    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 8
    )

    kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
    dilated = cv2.dilate(binary, kernel_horizontal, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    caixas_brutas = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w > 30 and h > 10:  # Descarta ruídos pequenos
            caixas_brutas.append((x, y, w, h))

    if not caixas_brutas:
        return {
            "titulo": "", "paragrafos": [], "elementos": [],
            "largura_pagina": largura_pagina, "altura_pagina": altura_pagina
        }

    caixas_brutas = sorted(caixas_brutas, key=lambda b: b[1])

    elementos_brutos = []
    alturas_caracteres = []

    for idx, (x, y, w, h) in enumerate(caixas_brutas):
        roi = gray[y:y + h, x:x + w]

        data = pytesseract.image_to_data(
            roi, lang='por', config='--psm 6', output_type=pytesseract.Output.DATAFRAME
        )
        df = data[data['text'].notnull() & (data['text'].str.strip() != '')]
        texto = " ".join(df['text'].astype(str)).strip() if not df.empty else ""

        if len(texto) <= 1:
            continue

        altura_char = float(df['height'].mean()) if not df.empty else float(h)
        alturas_caracteres.append(altura_char)

        elementos_brutos.append({
            "idx": idx, "texto": texto, "x": x, "y": y, "w": w, "h": h,
            "altura_char": altura_char
        })

    if not elementos_brutos:
        return {
            "titulo": "", "paragrafos": [], "elementos": [],
            "largura_pagina": largura_pagina, "altura_pagina": altura_pagina
        }

    media_h = float(np.mean(alturas_caracteres))
    std_h = float(np.std(alturas_caracteres)) if np.std(alturas_caracteres) > 0 else 1.0

    elementos_finais = []
    paragrafos_finais = []

    for b in elementos_brutos:
        x, y, w, h = b["x"], b["y"], b["w"], b["h"]
        altura_char = b["altura_char"]
        texto_limpo = analisador_lexico_corretor(b["texto"])

        z_score = (altura_char - media_h) / std_h

        if z_score > 1.2:
            estilo = "titulo"
        elif z_score > 0.6:
            estilo = "subtitulo"
        else:
            estilo = "normal"

        centro_x = x + (w / 2.0)
        centro_pag = largura_pagina / 2.0

        if abs(centro_x - centro_pag) < (largura_pagina * 0.12) and w < (largura_pagina * 0.80):
            alinhamento = "center"
        elif w > (largura_pagina * 0.65):
            alinhamento = "justify"
        elif x > (largura_pagina * 0.55):
            alinhamento = "right"
        else:
            alinhamento = "left"

        x_rel = round(x / largura_pagina, 4)
        y_rel = round(y / altura_pagina, 4)
        w_rel = round(w / largura_pagina, 4)
        h_rel = round(h / altura_pagina, 4)
        font_h_rel = round(altura_char / altura_pagina, 5)

        elementos_finais.append({
            "id": f"elem_{b['idx']}",
            "texto": texto_limpo,
            "alinhamento": alinhamento,
            "estilo": estilo,
            "altura_fonte_px": round(altura_char, 1),
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "x_relativo": x_rel,
            "y_relativo": y_rel,
            "width_relativo": w_rel,
            "height_relativo": h_rel,
            "altura_fonte_relativa": font_h_rel,
            "largura_pagina": largura_pagina,
            "altura_pagina": altura_pagina
        })

        paragrafos_finais.append(texto_limpo)

    titulos = [e["texto"] for e in elementos_finais if e["estilo"] == "titulo"]
    titulo_doc = titulos[0] if titulos else (paragrafos_finais[0] if paragrafos_finais else "Documento sem título")

    return {
        "titulo": titulo_doc,
        "paragrafos": paragrafos_finais,
        "elementos": elementos_finais,
        "largura_pagina": largura_pagina,
        "altura_pagina": altura_pagina
    }


def executar_pipeline_ocr(img_matriz):
    img_corrigida = deskew_hough_lines(img_matriz)


    layout = analisar_layout_morfologico_e_zscore(img_corrigida)


    texto_completo = "\n\n".join(layout["paragrafos"])
    suspeitas = extrair_sugestoes_e_palavras_suspeitas(texto_completo)

    return {
        "texto_completo_votado": texto_completo,
        "titulo": layout["titulo"],
        "paragrafos": layout["paragrafos"],
        "elementos": layout["elementos"],
        "palavras_suspeitas": suspeitas,
        "largura_pagina": layout["largura_pagina"],
        "altura_pagina": layout["altura_pagina"]
    }