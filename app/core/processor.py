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

