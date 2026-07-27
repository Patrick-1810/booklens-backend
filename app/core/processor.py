import cv2
import pytesseract
import pandas as pd
from collections import Counter
from spellchecker import SpellChecker

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

spell = SpellChecker(language='pt')


def detectar_e_rotacionar_por_borda(imagem_original):
    gray = cv2.cvtColor(imagem_original, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 200)

    contornos, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    angulo_final = 0.0

    if contornos:
        maior_contorno = max(contornos, key=cv2.contourArea)

        if cv2.contourArea(maior_contorno) > 5000:
            rect = cv2.minAreaRect(maior_contorno)
            angulo = rect[-1]

            if angulo < -45:
                angulo = 90 + angulo
            elif angulo > 45:
                angulo = angulo - 90

            if abs(angulo) < 45:
                angulo_final = angulo

    if abs(angulo_final) > 0.5:
        (h, w) = imagem_original.shape[:2]
        centro = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(centro, angulo_final, 1.0)
        imagem_original = cv2.warpAffine(
            imagem_original, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

    return imagem_original


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


def votacao_majoritaria_5_filtros(textos):
    listas_palavras = [t.split() for t in textos if t.strip()]
    if not listas_palavras:
        return ""

    max_len = max(len(l) for l in listas_palavras)
    resultado_final = []

    for i in range(max_len):
        candidatas = []
        for l in listas_palavras:
            if i < len(l):
                candidatas.append(l[i])

        if candidatas:
            contador = Counter(candidatas)
            mais_comum, freq = contador.most_common(1)[0]

            if freq >= 2:
                resultado_final.append(mais_comum)
            else:
                resultado_final.append(candidatas[0])

    return " ".join(resultado_final)


def analisar_layout_e_estruturar(imagem_binarizada):
    data = pytesseract.image_to_data(imagem_binarizada, lang='por', config='--psm 3',
                                     output_type=pytesseract.Output.DATAFRAME)

    df = data[data['text'].notnull() & (data['text'].str.strip() != '')].copy()

    if df.empty:
        return {"titulo": "", "paragrafos": []}

    linhas_agrupadas = []

    for (block_num, par_num, line_num), group in df.groupby(['block_num', 'par_num', 'line_num']):
        texto_linha = " ".join(group['text'].astype(str))
        top_medio = group['top'].mean()
        altura_media = group['height'].mean()

        linhas_agrupadas.append({
            'block_num': block_num,
            'par_num': par_num,
            'line_num': line_num,
            'texto': texto_linha,
            'top': top_medio,
            'height': altura_media
        })

    df_linhas = pd.DataFrame(linhas_agrupadas)

    if df_linhas.empty:
        return {"titulo": "", "paragrafos": []}

    altura_corte_topo = df_linhas['top'].min() + (df_linhas['top'].max() - df_linhas['top'].min()) * 0.35
    linhas_topo = df_linhas[df_linhas['top'] <= altura_corte_topo]

    if not linhas_topo.empty:
        idx_titulo = linhas_topo['height'].idxmax()
        linha_titulo = df_linhas.loc[idx_titulo]
        titulo_bruto = linha_titulo['texto']
        df_paragrafos = df_linhas.drop(idx_titulo)
    else:
        titulo_bruto = ""
        df_paragrafos = df_linhas

    paragrafos_brutos = []
    for (block, par), group in df_paragrafos.groupby(['block_num', 'par_num']):
        texto_paragrafo = " ".join(group['texto'].astype(str))
        if len(texto_paragrafo.strip()) > 3:
            paragrafos_brutos.append(texto_paragrafo)

    titulo_corrigido = analisador_lexico_corretor(titulo_bruto) if titulo_bruto else ""
    paragrafos_corrigidos = [analisador_lexico_corretor(p) for p in paragrafos_brutos]

    return {
        "titulo": titulo_corrigido,
        "paragrafos": paragrafos_corrigidos
    }


def executar_pipeline_ocr(img_matriz):
    img_corrigida = detectar_e_rotacionar_por_borda(img_matriz)

    img_grande = cv2.resize(img_corrigida, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img_grande, cv2.COLOR_BGR2GRAY)

    config_tesseract = r'--psm 3'


    # Filtro 1: Otsu
    _, f1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    texto1 = pytesseract.image_to_string(f1, lang='por', config=config_tesseract)

    # Filtro 2: Adaptativo Gaussiano
    f2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    texto2 = pytesseract.image_to_string(f2, lang='por', config=config_tesseract)

    # Filtro 3: Denoised + Adaptativo
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    f3 = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5)
    texto3 = pytesseract.image_to_string(f3, lang='por', config=config_tesseract)

    # Filtro 4: Threshold Adaptativo Média Simples
    f4 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 13, 4)
    texto4 = pytesseract.image_to_string(f4, lang='por', config=config_tesseract)

    # Filtro 5: CLAHE (Equalização de Contraste) + Otsu
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_clahe = clahe.apply(gray)
    _, f5 = cv2.threshold(img_clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    texto5 = pytesseract.image_to_string(f5, lang='por', config=config_tesseract)

    cv2.imwrite('../debbug_images/debug_f1_otsu.png', f1)
    cv2.imwrite('../debbug_images/debug_f2_adaptativo.png', f2)
    cv2.imwrite('../debbug_images/debug_f3_denoised.png', f3)
    cv2.imwrite('../debbug_images/debug_f4_mean.png', f4)
    cv2.imwrite('../debbug_images/debug_f5_clahe.png', f5)

    textos_filtros = [texto1, texto2, texto3, texto4, texto5]
    texto_votado = votacao_majoritaria_5_filtros(textos_filtros)
    texto_final_corrigido = analisador_lexico_corretor(texto_votado)

    estrutura = analisar_layout_e_estruturar(f5)

    return {
        "texto_completo_votado": texto_final_corrigido,
        "titulo": estrutura["titulo"],
        "paragrafos": estrutura["paragrafos"]
    }