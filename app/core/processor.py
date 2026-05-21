import cv2
import pytesseract
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extrair_com_filtros(img_path):
    img = cv2.imread(img_path)
    if img is None: return "Erro ao carregar"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    config_tesseract = r'--psm 3'

    _, f1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    texto1 = pytesseract.image_to_string(f1, lang='por', config=config_tesseract)

    f2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    texto2 = pytesseract.image_to_string(f2, lang='por', config=config_tesseract)

    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    f3 = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5)
    texto3 = pytesseract.image_to_string(f3, lang='por', config=config_tesseract)

    resultados = [texto1.strip(), texto2.strip(), texto3.strip()]
    melhor_resultado = max(resultados, key=len)

    return melhor_resultado

caminhos = ['../images_test/imagemBoa.jpeg', '../images_test/imagemRuim.jpeg']

for p in caminhos:
    print(f"\n--- Resultado para {p} ---")
    print(extrair_com_filtros(p))

