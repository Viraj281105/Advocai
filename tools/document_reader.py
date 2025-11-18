# tools/document_reader.py

from pypdf import PdfReader
from typing import List, Dict

# NOTE: For images/scans, you would integrate a local OCR tool here (e.g., Tesseract).
# For now, we focus on standard PDF text extraction using pypdf.

def extract_text_from_document(file_path: str) -> Dict:
    """
    Extracts text from a single PDF document. This tool is used by the 
    Auditor Agent to read the raw denial letter and policy documents.

    Args:
        file_path: The full file path to the PDF document.
        
    Returns:
        A dictionary containing the extracted text and file metadata.
    """
    try:
        reader = PdfReader(file_path)
        full_text = ""
        
        for i, page in enumerate(reader.pages):
            full_text += f"\n--- PAGE {i+1} ---\n"
            full_text += page.extract_text() or ""
            
        metadata = reader.metadata
        
        return {
            "source_file": file_path,
            "metadata": dict(metadata),
            "full_text_content": full_text.strip()
        }
        
    except FileNotFoundError:
        return {"error": f"File not found at path: {file_path}"}
    except Exception as e:
        return {"error": f"Failed to read document: {e}"}

# Example usage (for testing only)
if __name__ == '__main__':
    # You will need a test PDF file in your data/input folder to run this.
    print(extract_text_from_document("data/input/sample_denial.pdf"))