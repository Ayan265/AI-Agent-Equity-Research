import argparse
import sys
import json
import os
from core.pdf_processor import PDFProcessor
from documents.concalls.parser import ConcallParser

def extract_and_parse(pdf_path: str):
    """Core logic to extract PDF and parse into structured chunks"""
    print(f"[*] Extracting text from {pdf_path}...")
    pdf_processor = PDFProcessor(pdf_path)
    extracted_text = pdf_processor.extract_full_text()
    
    print(f"[*] Parsing transcript into Speaker-based Q&A chunks...")
    chunk_parser = ConcallParser()
    return chunk_parser.run_full_parsing(extracted_text)

def run_financial_report(structured_chunks: dict, output_path: str, overwrite: bool = False):
    """Runs the high-level Opening Remarks & Sentiment pipeline"""
    from documents.concalls.analyzer import AIAnalyzer
    from documents.concalls.formatter import ReportGenerator
    
    json_output_path = output_path if output_path.endswith('.json') else output_path + '.json'
    md_output_path = json_output_path.replace('.json', '_report.md')
    
    if not overwrite and os.path.exists(md_output_path):
        print(f"\n[!] {md_output_path} already exists. Skipping Financial Report to prevent overwriting.")
        return

    analyzer = AIAnalyzer()
    json_result = analyzer.analyze_chunks(structured_chunks)
    
    analyzer.save_analysis(json_result, json_output_path)
    
    generator = ReportGenerator()
    generator.generate_markdown(json_output_path, md_output_path)
    
    print(f"\n✅ Financial Report Complete!")
    print(f"📄 Report: {md_output_path}")

def run_deep_qa(structured_chunks: dict, output_path: str, overwrite: bool = False):
    """Runs the standalone detailed Q&A breakdown pipeline"""
    from documents.concalls.qa_extractor import QADeepExtractor
    from documents.concalls.qa_formatter import QADeepFormatter
    
    json_output_path = output_path if output_path.endswith('.json') else output_path + '.json'
    md_output_path = json_output_path.replace('.json', '_report.md')
    qa_sessions = structured_chunks.get("qa_sessions", [])
    
    existing_data = []
    if not overwrite and os.path.exists(md_output_path) and os.path.exists(json_output_path):
        # Auto-Resume Logic: Check if the report is actually complete
        try:
            with open(json_output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            if len(existing_data) >= len(qa_sessions):
                print(f"\n[!] {md_output_path} already exists and is COMPLETE. Skipping to prevent overwriting.")
                return
            else:
                print(f"\n[!] {md_output_path} is INCOMPLETE ({len(existing_data)}/{len(qa_sessions)} analysts). Auto-resuming extraction...")
        except Exception:
            existing_data = [] # If JSON is corrupted, start fresh
            
    # Track which analysts we already have data for
    processed_analysts = {str(item.get("analyst_name")).strip().lower() for item in existing_data if item and isinstance(item, dict) and "analyst_name" in item}
    
    qa_extractor = QADeepExtractor()
    all_interactions = list(existing_data) # Keep the good data we already extracted
    
    print(f"[*] Sending {len(qa_sessions) - len(processed_analysts)} missing Q&A blocks to AI Analyzer...")
    
    for i, qa in enumerate(qa_sessions):
        analyst = qa["analyst"]
        analyst_clean = str(analyst).strip().lower()
        
        if analyst_clean in processed_analysts:
            print(f"    -> Skipping {analyst} (Already Extracted in JSON)")
            continue
            
        print(f"    -> Extracting Q&A pairs for {analyst} ({i+1}/{len(qa_sessions)})")
        try:
            interaction_result = qa_extractor.analyze_qa_session(analyst, qa["discussion"])
            all_interactions.append(interaction_result)
        except Exception as e:
            print(f"    [!] Failed to analyze {analyst}: {e}")
            
    os.makedirs(os.path.dirname(os.path.abspath(json_output_path)), exist_ok=True)
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(all_interactions, f, indent=2)
        
    formatter = QADeepFormatter()
    formatter.generate_markdown(json_output_path, md_output_path)
    
    print(f"\n✅ Deep Q&A Report Complete!")
    print(f"📄 Report: {md_output_path}")

def process_single_pdf(pdf_path: str, output_path: str, task: str, overwrite: bool):
    try:
        # Step 1: Base Extraction (The Foundation)
        structured_chunks = extract_and_parse(pdf_path)
        
        # Step 2: Route to specific agentic task
        if task in ['financial_report', 'all']:
            # For financial_report, we append _data.json
            out_path = output_path + "_data.json" if not output_path.endswith('.json') else output_path.replace('.json', '_data.json')
            run_financial_report(structured_chunks, out_path, overwrite)
            
        if task in ['deep_qa', 'all']:
            # For deep_qa, we append _deep_qa.json
            out_path = output_path + "_deep_qa.json" if not output_path.endswith('.json') else output_path.replace('.json', '_deep_qa.json')
            run_deep_qa(structured_chunks, out_path, overwrite)

    except Exception as e:
        print(f"Error processing document {pdf_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Equity Research Agent - Omnivorous Document Processor")
    parser.add_argument('--pdf', required=False, help="Path to a single document.")
    parser.add_argument('--output', required=False, help="Base path to save the extracted data (e.g. extracts/wipro).")
    parser.add_argument('--input-dir', required=False, help="Path to a folder of raw PDFs to batch process & auto-route.")
    parser.add_argument('--output-dir', required=False, default="extracts/concalls", help="Base directory for auto-routed extracts.")
    parser.add_argument('--task', choices=['financial_report', 'deep_qa', 'all'], default='all', help="Which extraction task to run.")
    parser.add_argument('--overwrite', action='store_true', help="Force overwrite existing reports.")
    parser.add_argument('--compare', action='store_true', help="Run the multi-concall comparison tool.")
    parser.add_argument('--pdf1', required=False, help="First PDF to compare (e.g. data/concalls/Wipro/Wipro_Q3.pdf)")
    parser.add_argument('--pdf2', required=False, help="Second PDF to compare (e.g. data/concalls/Wipro/Wipro_Q4.pdf)")
    
    args = parser.parse_args()
    
    if args.compare:
        if not args.pdf1 or not args.pdf2:
            print("[!] You must provide both --pdf1 and --pdf2 to run a comparison.")
            sys.exit(1)
            
        comp1 = os.path.basename(os.path.dirname(args.pdf1))
        base1 = os.path.splitext(os.path.basename(args.pdf1))[0]
        json1 = os.path.join(args.output_dir, comp1, base1, base1 + "_data.json")
        
        comp2 = os.path.basename(os.path.dirname(args.pdf2))
        base2 = os.path.splitext(os.path.basename(args.pdf2))[0]
        json2 = os.path.join(args.output_dir, comp2, base2, base2 + "_data.json")
        
        if not os.path.exists(json1) or not os.path.exists(json2):
            print(f"[!] Cannot compare. Make sure BOTH PDFs have been fully processed first.")
            sys.exit(1)
            
        from documents.concalls.comparator import ConcallComparator
        comparator = ConcallComparator()
        output_report = os.path.join(args.output_dir, comp2, f"{base1}_vs_{base2}_comparison.md")
        comparator.generate_comparison_report(json1, json2, output_report)
        sys.exit(0)

    if not args.pdf and not args.input_dir:
        print("You must provide either --pdf or --input-dir")
        sys.exit(1)

    if args.input_dir:
        from core.document_router import DocumentRouter
        router = DocumentRouter()
        
        for root, _, files in os.walk(args.input_dir):
            for file in files:
                if file.lower().endswith(".pdf"):
                    raw_pdf_path = os.path.join(root, file)
                    print(f"\n{'='*50}\nProcessing File: {raw_pdf_path}\n{'='*50}")
                    
                    # 1. Auto-Rename and Route
                    routed_pdf_path = router.route_and_rename(raw_pdf_path)
                    
                    # 2. Determine auto output path
                    company = os.path.basename(os.path.dirname(routed_pdf_path))
                    basename = os.path.splitext(os.path.basename(routed_pdf_path))[0]
                    
                    # Target: extracts/concalls/Wipro/Wipro_Q4_FY26/Wipro_Q4_FY26
                    output_path = os.path.join(args.output_dir, company, basename, basename)
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    process_single_pdf(routed_pdf_path, output_path, args.task, args.overwrite)
    else:
        if not args.output:
            print("You must provide --output when processing a single --pdf")
            sys.exit(1)
        process_single_pdf(args.pdf, args.output, args.task, args.overwrite)

if __name__ == "__main__":
    main()
