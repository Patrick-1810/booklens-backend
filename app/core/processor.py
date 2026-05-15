import cv2
import pytesseract
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

img = cv2.imread('../images_test/imagemBoa.jpeg')

if img is None:
    print("Imagem não encontrada!")
else:

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    coords = np.column_stack(np.where(binary > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = binary.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(binary, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    config = r'--psm 3'

    try:
        texto = pytesseract.image_to_string(rotated, lang='por', config=config)
    except:
        print("Erro ao carregar em 'por', tentando 'eng'...")
        texto = pytesseract.image_to_string(rotated, lang='eng', config=config)

print("--- Texto Extraído ---")
print(texto)

cv2.imwrite('resultado_pdi_img_boa.png', rotated)