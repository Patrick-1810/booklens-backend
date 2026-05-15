import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

img = cv2.imread('images_test/imagem_teste.jpg')

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

texto = pytesseract.image_to_string(gray, lang='por')

print("--- Texto Extraído ---")
print(texto)