import json
import os
from core.api_client import APIClient

class ConcallComparator:
    def __init__(self):
        self.router = APIClient()

    def generate_comparison_report(self, report1_path: str, report2_path: str, output_path: str):
        print(f"\n{'='*50}\n[*] Generating Cross-Concall Comparison\n{'='*50}")
        print(f"    -> Concall 1: {os.path.basename(report1_path)}")
        print(f"    -> Concall 2: {os.path.basename(report2_path)}")
        
        with open(report1_path, 'r', encoding='utf-8') as f:
            data1 = json.load(f)
        with open(report2_path, 'r', encoding='utf-8') as f:
            data2 = json.load(f)
            
        prompt = f"""
You are an elite Equity Research Analyst. Your task is to compare two consecutive earnings calls for the same company and identify the key strategic and financial shifts.

=== Report 1 (Previous Quarter) ===
{json.dumps(data1, indent=2)[:50000]}

=== Report 2 (Current Quarter) ===
{json.dumps(data2, indent=2)[:50000]}

Please write a highly professional, formatting-rich Markdown report comparing the two quarters.
Focus on:
1. Metric Deltas (What went up/down, what guidance changed)
2. Tone Shifts (Did management sentiment become more optimistic or defensive?)
3. Strategic Pivots (What new initiatives were introduced in Quarter 2 that were missing in Quarter 1?)

Structure the response as a professional investment memo. Use markdown tables where appropriate. DO NOT output raw JSON.
"""
        
        # Use schema_class=None to return raw Markdown text
        print(f"    [*] Sending data to AI for synthesis...")
        markdown_result = self.router.extract_structured_json(prompt, schema_class=None)
        
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_result)
            
        print(f"    [✔] Successfully generated comparison report at: {output_path}")
