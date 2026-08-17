import pdfplumber
import os

class PDFProcessor:
    """
    A class dedicated to extracting text from PDF documents.
    Designed for Equity Research documents where retaining all data is critical.
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = os.path.abspath(pdf_path)
        
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")

    def extract_full_text(self) -> str:
        """
        Extracts all text from the PDF without aggressively stripping content,
        ensuring no critical financial data is accidentally lost.
        Returns the full transcript as a string.
        """
        print(f"[*] Extracting text from {os.path.basename(self.pdf_path)}...")
        full_text = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            total_pages = len(pdf.pages)
            
            for i, page in enumerate(pdf.pages):
                # Extract text exactly as it appears on the page
                text = page.extract_text()
                
                if text:
                    full_text.append(text.strip())
                    
        # Join pages with a single newline to save tokens, avoiding massive whitespace gaps
        final_transcript = "\n".join(full_text)
        print(f"[*] Successfully extracted {total_pages} pages.")
        
        return final_transcript

    def save_to_file(self, text: str, output_path: str):
        """
        Saves the extracted text to a specified output file.
        """
        abs_output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_output_path), exist_ok=True)
        
        with open(abs_output_path, "w", encoding="utf-8") as f:
            f.write(text)
            
        print(f"[*] Saved extracted text to: {abs_output_path}")

