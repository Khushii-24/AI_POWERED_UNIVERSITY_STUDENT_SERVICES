import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
import re

def parse_pdf(file_path_or_bytes):
    """
    Parse PDF into text. Uses PyMuPDF. If a page has little text, fallback to OCR.
    """
    if isinstance(file_path_or_bytes, bytes):
        doc = fitz.open(stream=file_path_or_bytes, filetype="pdf")
    else:
        doc = fitz.open(file_path_or_bytes)
        
    pages_text = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        
        # If less than 50 characters, assume it might be a scanned image and run OCR
        if len(text.strip()) < 50:
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            try:
                ocr_text = pytesseract.image_to_string(img)
                text = ocr_text
            except Exception as e:
                print(f"OCR failed for page {page_num}: {e}")
                
        pages_text.append({"page_num": page_num + 1, "text": text})
        
    return pages_text

def parse_txt(file_path_or_bytes):
    if isinstance(file_path_or_bytes, bytes):
        text = file_path_or_bytes.decode('utf-8')
    else:
        with open(file_path_or_bytes, 'r', encoding='utf-8') as f:
            text = f.read()
    return [{"page_num": 1, "text": text}]

def parse_document(file_name, file_content):
    if file_name.lower().endswith('.pdf'):
        return parse_pdf(file_content)
    elif file_name.lower().endswith('.txt') or file_name.lower().endswith('.md'):
        return parse_txt(file_content)
    else:
        # Fallback to txt parsing for unknown types for now
        return parse_txt(file_content)

def chunk_document(pages, metadata):
    """
    Section-aware chunking by clause/heading.
    """
    chunks = []
    current_section = "General"
    current_chunk = []
    
    for page in pages:
        lines = page["text"].split('\n')
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            # Simple heuristic for section headings: starts with digit(s) dot, or 'Annexure', etc.
            # e.g., "7.2 ", "Annexure A"
            if re.match(r'^(\d+\.\d+|\d+\.|Annexure|Section)\s+', line_stripped, re.IGNORECASE) and len(line_stripped) < 100:
                # If we have accumulated text, save the chunk
                if current_chunk:
                    chunk_text = "\\n".join(current_chunk)
                    chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            **metadata,
                            "section": current_section,
                            "page": page["page_num"]
                        }
                    })
                    current_chunk = []
                current_section = line_stripped
                
            current_chunk.append(line_stripped)
            
            # If chunk is getting too large, break it (overlap fallback)
            if len("\\n".join(current_chunk)) > 1000:
                chunk_text = "\\n".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        **metadata,
                        "section": current_section,
                        "page": page["page_num"]
                    }
                })
                # Keep an overlap
                current_chunk = current_chunk[-3:]
                
        # End of page chunking
        if current_chunk:
            chunk_text = "\\n".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    **metadata,
                    "section": current_section,
                    "page": page["page_num"]
                }
            })
            current_chunk = []
            
    return chunks
