import fitz
import pytesseract
from PIL import Image
import io
from app.core.config import settings

pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH

# Change this to your actual uploaded PDF path
file_path = "uploads/servlets.pdf"
start_page = 1
end_page = 3

doc = fitz.open(file_path)
for page_num in range(start_page - 1, end_page):
    page = doc[page_num]
    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes))
    text = pytesseract.image_to_string(img)
    print(f"--- Page {page_num + 1} ---")
    print(text)
    print()

doc.close()