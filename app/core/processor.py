import re
import cv2
import numpy as np
import pytesseract

from spellchecker import SpellChecker


# ============================================================
# CONFIGURAÇÕES
# ============================================================

TESSERACT_CONFIG_GLOBAL = "--oem 3 --psm 3"
TESSERACT_CONFIG_SPARSE = "--oem 3 --psm 11"

spell = SpellChecker(language="pt")


# ============================================================
# REGEX
# ============================================================

EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

URL_REGEX = re.compile(
    r"^(https?://|www\.|[A-Za-z0-9.-]+\.)"
)

PHONE_REGEX = re.compile(
    r"^[\d\s()+\-./]{8,}$"
)

DATE_REGEX = re.compile(
    r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$"
)

NUMBER_REGEX = re.compile(
    r"^[\d.,:/%-]+$"
)

NOISE_REGEX = re.compile(
    r"[€$@%&*#\\/<>_{}\[\]\|]"
)


# ============================================================
# DESKEW
# ============================================================

def deskew_hough_lines(image):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(
        gray,
        50,
        150,
        apertureSize=3
    )

    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=80,
        minLineLength=max(80, image.shape[1] // 10),
        maxLineGap=20
    )

    if lines is None:
        return image

    angles = []

    for line in lines:
        x1, y1, x2, y2 = line[0]

        angle = np.degrees(
            np.arctan2(
                y2 - y1,
                x2 - x1
            )
        )

        # Considera somente linhas aproximadamente horizontais
        if -10 < angle < 10:
            angles.append(angle)

    if not angles:
        return image

    angle = float(np.median(angles))

    if abs(angle) < 0.2:
        return image

    h, w = image.shape[:2]

    center = (w // 2, h // 2)

    matrix = cv2.getRotationMatrix2D(
        center,
        angle,
        1.0
    )

    corrected = cv2.warpAffine(
        image,
        matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )

    return corrected


# ============================================================
# PRÉ-PROCESSAMENTO
# ============================================================

def preprocess_document(image):

    # -----------------------------------------
    # Upscale
    # -----------------------------------------

    upscale = cv2.resize(
        image,
        None,
        fx=2.0,
        fy=2.0,
        interpolation=cv2.INTER_CUBIC
    )

    # -----------------------------------------
    # Escala de cinza
    # -----------------------------------------

    gray = cv2.cvtColor(
        upscale,
        cv2.COLOR_BGR2GRAY
    )

    # -----------------------------------------
    # Redução leve de ruído
    # -----------------------------------------

    denoised = cv2.fastNlMeansDenoising(
        gray,
        None,
        h=8,
        templateWindowSize=7,
        searchWindowSize=21
    )

    # -----------------------------------------
    # CLAHE
    # -----------------------------------------

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(
        denoised
    )

    # -----------------------------------------
    # OTSU
    # -----------------------------------------

    _, binary_otsu = cv2.threshold(
        enhanced,
        0,
        255,
        cv2.THRESH_BINARY,
        cv2.THRESH_OTSU
    )

    # -----------------------------------------
    # ADAPTIVE THRESHOLD
    # -----------------------------------------

    binary_adaptive = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )

    return {
        "original": upscale,
        "gray": gray,
        "enhanced": enhanced,
        "binary_otsu": binary_otsu,
        "binary_adaptive": binary_adaptive
    }


# ============================================================
# LIMPEZA DE TEXTO
# ============================================================

def normalizar_texto(texto):
    if not texto:
        return ""

    texto = str(texto)

    # Espaços duplicados
    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    # Espaços antes de pontuação
    texto = re.sub(
        r"\s+([,.!?;:])",
        r"\1",
        texto
    )

    return texto.strip()


# ============================================================
# IDENTIFICAÇÃO DE TEXTO ESPECIAL
# ============================================================

def eh_email(texto):
    return bool(
        EMAIL_REGEX.match(
            texto.strip()
        )
    )


def eh_url(texto):
    return bool(
        URL_REGEX.match(
            texto.strip()
        )
    )


def eh_telefone(texto):
    return bool(
        PHONE_REGEX.match(
            texto.strip()
        )
    )


def eh_data(texto):
    return bool(
        DATE_REGEX.match(
            texto.strip()
        )
    )


def eh_numero(texto):
    return bool(
        NUMBER_REGEX.match(
            texto.strip()
        )
    )


def deve_proteger_correcao(texto):

    texto = texto.strip()

    if not texto:
        return True

    if eh_email(texto):
        return True

    if eh_url(texto):
        return True

    if eh_telefone(texto):
        return True

    if eh_data(texto):
        return True

    if eh_numero(texto):
        return True

    # Siglas
    if texto.isupper() and len(texto) <= 10:
        return True

    # Palavras contendo números
    if any(char.isdigit() for char in texto):
        return True

    return False


# ============================================================
# CORRETOR ORTOGRÁFICO SELETIVO
# ============================================================

def corrigir_palavra(palavra):

    if deve_proteger_correcao(palavra):
        return palavra

    limpa = re.sub(
        r"[^\wÀ-ÿ-]",
        "",
        palavra,
        flags=re.UNICODE
    )

    if not limpa:
        return palavra

    # Palavras muito pequenas são perigosas para correção
    if len(limpa) <= 2:
        return palavra

    if limpa.lower() in spell:
        return palavra

    sugestao = spell.correction(
        limpa.lower()
    )

    if not sugestao:
        return palavra

    # Evita correções absurdas
    if abs(len(sugestao) - len(limpa)) > 3:
        return palavra

    if palavra[0].isupper():
        sugestao = sugestao.capitalize()

    return palavra.replace(
        limpa,
        sugestao
    )


def corrigir_texto_seletivamente(texto):
    palavras = texto.split()

    resultado = []

    for palavra in palavras:
        resultado.append(
            corrigir_palavra(
                palavra
            )
        )

    return " ".join(resultado)


# ============================================================
# DETECÇÃO DE SUSPEITAS
# ============================================================

def extrair_sugestoes_e_palavras_suspeitas(texto):
    tokens = texto.split()

    suspeitas = []

    for i, token in enumerate(tokens):

        token_limpo = token.strip()

        if not token_limpo:
            continue

        # Não marcar URLs / emails
        if deve_proteger_correcao(token_limpo):
            continue

        suspeita = False

        # Caracteres estranhos
        if NOISE_REGEX.search(
            token_limpo
        ):
            suspeita = True

        # Palavra muito curta com símbolos
        elif (
            len(token_limpo) <= 3
            and not token_limpo.isalnum()
        ):
            suspeita = True

        # Sequência de caracteres estranha
        elif re.search(
            r"[A-Za-zÀ-ÿ]{1,2}[^A-Za-zÀ-ÿ\s]{2,}",
            token_limpo
        ):
            suspeita = True

        if suspeita:

            original = re.sub(
                r"^[^\wÀ-ÿ]+|[^\wÀ-ÿ]+$",
                "",
                token_limpo
            )

            if original:

                sugestoes = []

                correcao = corrigir_palavra(
                    original
                )

                if (
                    correcao
                    and correcao.lower()
                    != original.lower()
                ):
                    sugestoes.append(
                        correcao
                    )

                suspeitas.append({
                    "original": original,
                    "sugestoes": sugestoes
                })

    # Remove duplicadas
    unicas = []
    vistas = set()

    for item in suspeitas:

        chave = item["original"].lower()

        if chave not in vistas:

            vistas.add(chave)

            unicas.append(
                item
            )

    return unicas


# ============================================================
# OCR GLOBAL
# ============================================================

def executar_ocr_global(imagem):

    data = pytesseract.image_to_data(
        imagem,
        lang="por",
        config=TESSERACT_CONFIG_GLOBAL,
        output_type=pytesseract.Output.DICT
    )

    palavras = []

    quantidade = len(
        data["text"]
    )

    for i in range(
        quantidade
    ):

        texto = str(
            data["text"][i]
        ).strip()

        if not texto:
            continue

        try:
            conf = float(
                data["conf"][i]
            )
        except Exception:
            conf = 0.0

        if conf < 5:
            continue

        palavras.append({
            "text": texto,
            "x": int(data["left"][i]),
            "y": int(data["top"][i]),
            "w": int(data["width"][i]),
            "h": int(data["height"][i]),
            "conf": conf,
            "block_num": int(data["block_num"][i]),
            "par_num": int(data["par_num"][i]),
            "line_num": int(data["line_num"][i]),
            "word_num": int(data["word_num"][i])
        })

    return palavras


# ============================================================
# AGRUPAMENTO POR LINHAS
# ============================================================

def agrupar_palavras_em_linhas(palavras):

    grupos = {}

    for palavra in palavras:

        chave = (
            palavra["block_num"],
            palavra["par_num"],
            palavra["line_num"]
        )

        if chave not in grupos:
            grupos[chave] = []

        grupos[chave].append(
            palavra
        )

    linhas = []

    for chave, palavras_linha in grupos.items():

        palavras_linha.sort(
            key=lambda item: item["x"]
        )

        x1 = min(
            p["x"]
            for p in palavras_linha
        )

        y1 = min(
            p["y"]
            for p in palavras_linha
        )

        x2 = max(
            p["x"] + p["w"]
            for p in palavras_linha
        )

        y2 = max(
            p["y"] + p["h"]
            for p in palavras_linha
        )

        texto = " ".join(
            p["text"]
            for p in palavras_linha
        )

        confianca = np.mean(
            [
                p["conf"]
                for p in palavras_linha
            ]
        )

        linhas.append({
            "texto": normalizar_texto(texto),
            "x": x1,
            "y": y1,
            "w": x2 - x1,
            "h": y2 - y1,
            "confianca": round(
                float(confianca),
                2
            ),
            "palavras": palavras_linha,
            "block_num": chave[0],
            "par_num": chave[1],
            "line_num": chave[2]
        })

    linhas.sort(
        key=lambda linha: (
            linha["y"],
            linha["x"]
        )
    )

    return linhas


# ============================================================
# AGRUPAMENTO ESPACIAL DE LINHAS
# ============================================================

def agrupar_linhas_em_blocos(
    linhas,
    largura_pagina,
    altura_pagina
):

    if not linhas:
        return []

    alturas = [
        linha["h"]
        for linha in linhas
        if linha["h"] > 0
    ]

    altura_media = (
        float(np.median(alturas))
        if alturas
        else 20
    )

    blocos = []
    bloco_atual = []

    for linha in linhas:

        if not bloco_atual:
            bloco_atual.append(
                linha
            )
            continue

        anterior = bloco_atual[-1]

        fim_anterior = (
            anterior["y"]
            + anterior["h"]
        )

        inicio_atual = linha["y"]

        espaco = (
            inicio_atual
            - fim_anterior
        )

        # Diferença horizontal
        inicio_anterior = anterior["x"]

        diferenca_x = abs(
            linha["x"]
            - inicio_anterior
        )

        # Critério de agrupamento
        mesma_regiao_vertical = (
            espaco <= altura_media * 1.8
        )

        mesma_regiao_horizontal = (
            diferenca_x
            <= largura_pagina * 0.35
        )

        if (
            mesma_regiao_vertical
            and mesma_regiao_horizontal
        ):
            bloco_atual.append(
                linha
            )
        else:
            blocos.append(
                bloco_atual
            )

            bloco_atual = [
                linha
            ]

    if bloco_atual:
        blocos.append(
            bloco_atual
        )

    return blocos


# ============================================================
# DETECÇÃO DE ALINHAMENTO
# ============================================================

def detectar_alinhamento(
    linhas,
    largura_pagina
):

    if not linhas:
        return "left"

    centros = [
        linha["x"] + (
            linha["w"] / 2
        )
        for linha in linhas
    ]

    inicios = [
        linha["x"]
        for linha in linhas
    ]

    finais = [
        linha["x"] + linha["w"]
        for linha in linhas
    ]

    centro_medio = float(
        np.mean(centros)
    )

    inicio_medio = float(
        np.mean(inicios)
    )

    final_medio = float(
        np.mean(finais)
    )

    # -----------------------------------------
    # Centralizado
    # -----------------------------------------

    distancia_centro = abs(
        centro_medio
        - largura_pagina / 2
    )

    if (
        distancia_centro
        < largura_pagina * 0.08
    ):

        variacao_inicio = np.std(
            inicios
        )

        if (
            variacao_inicio
            < largura_pagina * 0.08
        ):
            return "center"

    # -----------------------------------------
    # Esquerda
    # -----------------------------------------

    if (
        inicio_medio
        < largura_pagina * 0.30
    ):
        return "left"

    # -----------------------------------------
    # Direita
    # -----------------------------------------

    if (
        final_medio
        > largura_pagina * 0.75
    ):
        return "right"

    # -----------------------------------------
    # Justificado
    # -----------------------------------------

    if len(linhas) >= 2:

        larguras = [
            linha["w"]
            for linha in linhas
        ]

        largura_media = np.mean(
            larguras
        )

        if (
            largura_media
            > largura_pagina * 0.55
        ):
            return "justify"

    return "left"


# ============================================================
# CLASSIFICAÇÃO DE LISTA
# ============================================================

def detectar_lista(texto):

    padroes = [
        r"^[•●▪◦\-–—]\s+",
        r"^\d+[\.)]\s+",
        r"^[a-zA-Z][\.)]\s+"
    ]

    for padrao in padroes:

        if re.match(
            padrao,
            texto
        ):
            return True

    return False


# ============================================================
# CLASSIFICAÇÃO SEMÂNTICA
# ============================================================

def classificar_bloco(
    bloco,
    altura_media_global,
    largura_pagina,
    altura_pagina
):

    linhas = bloco

    texto = " ".join(
        linha["texto"]
        for linha in linhas
    )

    texto = normalizar_texto(
        texto
    )

    alturas = [
        linha["h"]
        for linha in linhas
        if linha["h"] > 0
    ]

    altura_media = (
        float(np.mean(alturas))
        if alturas
        else altura_media_global
    )

    primeira_linha = linhas[0]

    centro_x = (
        primeira_linha["x"]
        + primeira_linha["w"] / 2
    )

    z_score = (
        altura_media
        - altura_media_global
    ) / max(
        altura_media_global,
        1
    )

    # -----------------------------------------
    # Lista
    # -----------------------------------------

    if any(
        detectar_lista(
            linha["texto"]
        )
        for linha in linhas
    ):
        return "list"

    # -----------------------------------------
    # Muito grande = título
    # -----------------------------------------

    if z_score > 1.8:
        return "title"

    # -----------------------------------------
    # Grande = heading
    # -----------------------------------------

    if z_score > 0.9:
        return "heading"

    # -----------------------------------------
    # Texto centralizado próximo ao topo
    # -----------------------------------------

    if (
        abs(
            centro_x
            - largura_pagina / 2
        )
        < largura_pagina * 0.08
        and primeira_linha["y"]
        < altura_pagina * 0.30
    ):

        if len(texto) < 180:
            return "heading"

    # -----------------------------------------
    # Caixa curta em maiúsculas
    # -----------------------------------------

    letras = re.sub(
        r"[^A-Za-zÀ-ÿ]",
        "",
        texto
    )

    if letras:

        proporcao_upper = sum(
            c.isupper()
            for c in letras
        ) / len(letras)

        if (
            proporcao_upper > 0.75
            and len(texto) < 150
        ):
            return "heading"

    # -----------------------------------------
    # Normal
    # -----------------------------------------

    return "paragraph"


# ============================================================
# CONSTRUIR ELEMENTOS
# ============================================================

def construir_elementos(
    blocos,
    largura_pagina,
    altura_pagina
):

    todas_alturas = []

    for bloco in blocos:
        for linha in bloco:
            todas_alturas.append(
                linha["h"]
            )

    altura_media_global = (
        float(np.median(todas_alturas))
        if todas_alturas
        else 20
    )

    elementos = []

    for indice, bloco in enumerate(
        blocos
    ):

        if not bloco:
            continue

        # -----------------------------------------
        # Bounding box
        # -----------------------------------------

        x1 = min(
            linha["x"]
            for linha in bloco
        )

        y1 = min(
            linha["y"]
            for linha in bloco
        )

        x2 = max(
            linha["x"]
            + linha["w"]
            for linha in bloco
        )

        y2 = max(
            linha["y"]
            + linha["h"]
            for linha in bloco
        )

        texto_original = " ".join(
            linha["texto"]
            for linha in bloco
        )

        texto_original = normalizar_texto(
            texto_original
        )

        # -----------------------------------------
        # Correção seletiva
        # -----------------------------------------

        texto_corrigido = (
            corrigir_texto_seletivamente(
                texto_original
            )
        )

        # -----------------------------------------
        # Classificação
        # -----------------------------------------

        estilo = classificar_bloco(
            bloco,
            altura_media_global,
            largura_pagina,
            altura_pagina
        )

        alinhamento = detectar_alinhamento(
            bloco,
            largura_pagina
        )

        # -----------------------------------------
        # Confiança média
        # -----------------------------------------

        confiancas = [
            linha["confianca"]
            for linha in bloco
        ]

        confianca = (
            float(np.mean(confiancas))
            if confiancas
            else 0
        )

        # -----------------------------------------
        # Altura média da fonte
        # -----------------------------------------

        alturas = [
            palavra["h"]
            for linha in bloco
            for palavra in linha["palavras"]
        ]

        altura_fonte = (
            float(np.mean(alturas))
            if alturas
            else 0
        )

        # -----------------------------------------
        # Coordenadas relativas
        # -----------------------------------------

        x_rel = round(
            x1 / largura_pagina,
            5
        )

        y_rel = round(
            y1 / altura_pagina,
            5
        )

        width_rel = round(
            (x2 - x1)
            / largura_pagina,
            5
        )

        height_rel = round(
            (y2 - y1)
            / altura_pagina,
            5
        )

        font_rel = round(
            altura_fonte
            / altura_pagina,
            6
        )

        elemento = {
            "id": f"elem_{indice + 1}",

            "tipo": estilo,

            "texto": texto_corrigido,

            "texto_original": texto_original,

            "alinhamento": alinhamento,

            "confianca_ocr": round(
                confianca,
                2
            ),

            "altura_fonte_px": round(
                altura_fonte,
                2
            ),

            "x": int(x1),
            "y": int(y1),

            "width": int(
                x2 - x1
            ),

            "height": int(
                y2 - y1
            ),

            "x_relativo": x_rel,
            "y_relativo": y_rel,

            "width_relativo": width_rel,
            "height_relativo": height_rel,

            "altura_fonte_relativa": font_rel,

            "numero_linhas": len(
                bloco
            ),

            "largura_pagina": largura_pagina,
            "altura_pagina": altura_pagina
        }

        elementos.append(
            elemento
        )

    return elementos


# ============================================================
# ESCOLHA DA MELHOR IMAGEM PARA OCR
# ============================================================

def escolher_melhor_preprocessamento(
    imagens
):

    melhor_imagem = None
    melhor_confianca = -1

    for nome, imagem in imagens.items():

        if nome == "original":
            continue

        try:

            data = pytesseract.image_to_data(
                imagem,
                lang="por",
                config=TESSERACT_CONFIG_GLOBAL,
                output_type=pytesseract.Output.DICT
            )

            confiancas = []

            for conf in data["conf"]:

                try:
                    valor = float(conf)

                    if valor > 0:
                        confiancas.append(
                            valor
                        )

                except Exception:
                    continue

            if not confiancas:
                continue

            media = float(
                np.mean(confiancas)
            )

            if media > melhor_confianca:

                melhor_confianca = media
                melhor_imagem = imagem

        except Exception:
            continue

    if melhor_imagem is None:
        melhor_imagem = imagens["enhanced"]

    return (
        melhor_imagem,
        melhor_confianca
    )


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

def executar_pipeline_ocr(img_matriz):

    # ========================================================
    # DESKEW
    # ========================================================

    img_corrigida = deskew_hough_lines(
        img_matriz
    )

    # ========================================================
    # PRÉ-PROCESSAMENTO
    # ========================================================

    preprocessados = preprocess_document(
        img_corrigida
    )

    # ========================================================
    # ESCOLHER MELHOR REPRESENTAÇÃO
    # ========================================================

    imagem_ocr, confianca_preprocessamento = (
        escolher_melhor_preprocessamento(
            preprocessados
        )
    )

    # ========================================================
    # OCR GLOBAL
    # ========================================================

    palavras = executar_ocr_global(
        imagem_ocr
    )

    # ========================================================
    # Se não encontrou texto
    # ========================================================

    if not palavras:

        altura, largura = (
            imagem_ocr.shape[:2]
        )

        return {
            "texto_completo_votado": "",
            "titulo": "Documento sem título",
            "paragrafos": [],
            "elementos": [],
            "palavras_suspeitas": [],
            "largura_pagina": largura,
            "altura_pagina": altura,
            "confianca_preprocessamento": 0
        }

    # ========================================================
    # LINHAS
    # ========================================================

    linhas = agrupar_palavras_em_linhas(
        palavras
    )

    # ========================================================
    # BLOCOS
    # ========================================================

    altura, largura = (
        imagem_ocr.shape[:2]
    )

    blocos = agrupar_linhas_em_blocos(
        linhas,
        largura,
        altura
    )

    # ========================================================
    # ELEMENTOS
    # ========================================================

    elementos = construir_elementos(
        blocos,
        largura,
        altura
    )

    # ========================================================
    #  ORDENAÇÃO
    # ========================================================

    elementos.sort(
        key=lambda elemento: (
            elemento["y"],
            elemento["x"]
        )
    )

    # ========================================================
    # TEXTO COMPLETO
    # ========================================================

    paragrafos = [
        elemento["texto"]
        for elemento in elementos
        if elemento["texto"].strip()
    ]

    texto_completo = "\n\n".join(
        paragrafos
    )

    # ========================================================
    #  TÍTULO
    # ========================================================

    candidatos_titulo = [
        elemento
        for elemento in elementos
        if elemento["tipo"]
        in ["title", "heading"]
    ]

    if candidatos_titulo:

        candidatos_titulo.sort(
            key=lambda elemento: (
                elemento["y"],
                -elemento[
                    "altura_fonte_px"
                ]
            )
        )

        titulo = candidatos_titulo[0][
            "texto"
        ]

    elif elementos:

        titulo = elementos[0][
            "texto"
        ]

    else:

        titulo = "Documento sem título"

    # ========================================================
    # SUSPEITAS
    # ========================================================

    suspeitas = (
        extrair_sugestoes_e_palavras_suspeitas(
            texto_completo
        )
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    return {

        "texto_completo_votado":
            texto_completo,

        "titulo":
            titulo,

        "paragrafos":
            paragrafos,

        "elementos":
            elementos,

        "palavras_suspeitas":
            suspeitas,

        "largura_pagina":
            largura,

        "altura_pagina":
            altura,

        "confianca_preprocessamento":
            round(
                confianca_preprocessamento,
                2
            )
    }