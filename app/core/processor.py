import cv2
import pytesseract
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

    return texto_final_corrigido