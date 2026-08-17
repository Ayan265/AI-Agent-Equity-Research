import os
import shutil
import pdfplumber
import json
from pydantic import BaseModel, Field
from core.api_client import APIClient

class DocumentMetadata(BaseModel):
    company_name: str = Field(description="The simple name of the company without legal suffixes, e.g. Wipro, Infosys, Apple")
    quarter: str = Field(description="The financial quarter, e.g. Q1, Q2, Q3, Q4")
    year: str = Field(description="The financial year, e.g. FY26, FY24")

class DocumentRouter:
    """
    Intakes raw PDFs, parses the first page via AI, and automatically 
    renames and sorts them into professional directories.
    """
    def __init__(self, base_data_dir: str = "data/concalls"):
        self.base_data_dir = os.path.abspath(base_data_dir)
        self.api_client = APIClient()

    def route_and_rename(self, raw_pdf_path: str) -> str:
        """
        Reads the first page of the raw PDF, extracts metadata via AI,
        renames the file, and moves it to the appropriate data directory.
        Returns the absolute path to the newly renamed file.
        """
        abs_raw_path = os.path.abspath(raw_pdf_path)
        print(f"[*] Analyzing raw document for routing: {os.path.basename(abs_raw_path)}...")
        
        # Read the first page
        try:
            with pdfplumber.open(abs_raw_path) as pdf:
                if len(pdf.pages) == 0:
                    raise Exception("PDF has no pages.")
                first_page_text = pdf.pages[0].extract_text()
                
                if not first_page_text:
                    # Try second page if first is an empty cover
                    if len(pdf.pages) > 1:
                        first_page_text = pdf.pages[1].extract_text()
        except Exception as e:
            print(f"    [!] Failed to read PDF {abs_raw_path}: {e}")
            return abs_raw_path # Return original if failed
            
        prompt = f"""
You are a highly accurate data extraction assistant.
Please identify the Company Name, Quarter, and Financial Year from the following text (which is the cover page of an earnings call transcript).
If the quarter or year is not explicitly stated in the text, try to infer it from the date or context.
Return ONLY valid JSON matching the schema.

Transcript Cover Page:
{first_page_text[:1500]}
"""
        
        try:
            # Pass the prompt to API Client. 
            response_json = self.api_client.extract_structured_json(prompt, DocumentMetadata) 
            metadata = json.loads(response_json)
            
            # Format the new filename: Company_Quarter_Year.pdf
            # e.g., Wipro_Q4_FY26.pdf
            company = str(metadata.get("company_name", "Unknown")).strip().replace(" ", "")
            quarter = str(metadata.get("quarter", "Unknown")).strip().replace(" ", "")
            year = str(metadata.get("year", "Unknown")).strip().replace(" ", "")
            
            new_filename = f"{company}_{quarter}_{year}.pdf"
            
            # Create the target directory: data/concalls/Wipro/
            target_dir = os.path.join(self.base_data_dir, company)
            os.makedirs(target_dir, exist_ok=True)
            
            target_path = os.path.join(target_dir, new_filename)
            
            # If the file is already exactly there, do nothing
            if os.path.abspath(abs_raw_path) == os.path.abspath(target_path):
                print(f"    [✔] Document is already correctly named and routed: {target_path}")
                return target_path
                
            # If file with new name already exists, maybe append a suffix or just overwrite
            if os.path.exists(target_path) and os.path.abspath(abs_raw_path) != os.path.abspath(target_path):
                 print(f"    [!] {new_filename} already exists in {target_dir}. Overwriting.")
                 
            # Move and rename the file
            shutil.move(abs_raw_path, target_path)
            print(f"    [✔] Successfully renamed and routed to: {target_path}")
            
            return target_path
            
        except Exception as e:
            print(f"    [!] Failed to route document via AI: {e}")
            return abs_raw_path # Fallback to original
