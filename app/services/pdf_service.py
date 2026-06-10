import fitz  # pymupdf
import pytesseract
from PIL import Image
import io
from app.core.config import settings

pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH

def extract_pages_as_images(file_path: str, start_page: int, end_page: int) -> list:
    """Slice PDF pages and convert to images."""
    doc = fitz.open(file_path)
    images = []

    for page_num in range(start_page - 1, end_page):  # fitz is 0-indexed
        page = doc[page_num]
        mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR quality
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        images.append(img)

    doc.close()
    return images

def ocr_images(images: list) -> str:
    """Run OCR on a list of images and return combined text."""
    full_text = ""
    for img in images:
        text = pytesseract.image_to_string(img)
        full_text += text + "\n\n"
    return full_text.strip()

def clean_text(text: str) -> str:
    """Basic cleanup of OCR output."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if len(line) > 2:  # skip empty or garbage lines
            cleaned.append(line)
    return "\n".join(cleaned)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks