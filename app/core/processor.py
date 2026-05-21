import cv2
import pytesseract
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def rotacionar_texto(imagem_binaria, imagem_original):
    edges = cv2.Canny(imagem_binaria, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)

    angulos = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angulo = np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi
            if -45 < angulo < 45:
                angulos.append(angulo)

    angulo_final = np.median(angulos) if len(angulos) > 0 else 0.0

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

def executar_pipeline_ocr(img_matriz):

    img_grande = cv2.resize(img_matriz, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img_grande, cv2.COLOR_BGR2GRAY)
    denoised_base = cv2.fastNlMeansDenoising(gray, h=10)

    temp_bin = cv2.adaptiveThreshold(denoised_base, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    gray_corrigido = rotacionar_texto(temp_bin, denoised_base)

    config_tesseract = r'--psm 3'

    _, f1 = cv2.threshold(gray_corrigido, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    texto1 = pytesseract.image_to_string(f1, lang='por', config=config_tesseract)

    f2 = cv2.adaptiveThreshold(gray_corrigido, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    texto2 = pytesseract.image_to_string(f2, lang='por', config=config_tesseract)

    denoised = cv2.fastNlMeansDenoising(gray_corrigido, h=10)
    f3 = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5)
    texto3 = pytesseract.image_to_string(f3, lang='por', config=config_tesseract)

    resultados = [texto1.strip(), texto2.strip(), texto3.strip()]
    melhor_resultado = max(resultados, key=len)

    cv2.imwrite('debug_f1_otsu_1.png', f1)
    cv2.imwrite('debug_f2_adaptativo_2.png', f2)
    cv2.imwrite('debug_f3_denoised_3.png', f3)

    return melhor_resultado

if __name__ == "__main__":
    caminhos = ['../images_test/imagemBoa.jpeg', '../images_test/imagemRuim.jpeg']
    for p in caminhos:
        img_teste = cv2.imread(p)
        if img_teste is not None:
            print(f"\n--- Teste Local para {p} ---")
            print(executar_pipeline_ocr(img_teste))
        else:
            print(f"Erro ao carregar o arquivo de teste local: {p}")