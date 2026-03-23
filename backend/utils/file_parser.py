import os
import pandas as pd
import fitz
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def parse_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return parse_csv(file_path)
    elif ext in [".xlsx", ".xls"]:
        return parse_excel(file_path)
    elif ext == ".pdf":
        return parse_pdf(file_path)
    elif ext in [".png", ".jpg", ".jpeg"]:
        return parse_image(file_path)
    elif ext == ".txt":
        return parse_txt(file_path)
    else:
        return "Unsupported file type."

def parse_csv(path):
    df = pd.read_csv(path)
    return df.to_string(index=False)

def parse_excel(path):
    df = pd.read_excel(path)
    return df.to_string(index=False)

def parse_pdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

def parse_image(path):
    img = Image.open(path)
    text = pytesseract.image_to_string(img)
    return text.strip()

def parse_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()