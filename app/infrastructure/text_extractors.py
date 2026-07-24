import os
import docx
import fitz
import pandas as pd
import easyocr

reader = easyocr.Reader(['id', 'en'], gpu=False)

def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == '.docx':
            return '\n'.join([p.text for p in docx.Document(file_path).paragraphs])
        elif ext == '.pdf':
            text = ""
            with fitz.open(file_path) as doc:
                for page in doc: 
                    text += page.get_text()
            return text
        elif ext in ['.xlsx', '.xls', '.csv']:
            df = pd.read_excel(file_path) if ext.startswith('.xl') else pd.read_csv(file_path)
            return "Data Tabel: " + df.head(10).to_string()
        elif ext in ['.png', '.jpg', '.jpeg']:
            return ' '.join(reader.readtext(file_path, detail=0))
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None
    return None