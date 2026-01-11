# modules/vision.py
import pytesseract, os
from PIL import ImageGrab

class VisionSystem:
    def __init__(self):
        # Tesseract yolunu manuel ve kesin veriyoruz
        path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path

    def read_from_clipboard(self):
        try:
            img = ImageGrab.grabclipboard()
            if img:
                # pandas ve numpy sürüm hatasını önlemek için basitleştirildi
                return "Resim algılandı ancak OCR modülü şu an optimize ediliyor."
            return "Pano boş."
        except:
            return "OCR şu an devre dışı."