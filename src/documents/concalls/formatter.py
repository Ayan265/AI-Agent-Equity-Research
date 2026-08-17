import json
import os

class ReportGenerator:
    """
    Takes the structured JSON output from the AIAnalyzer and formats it into
    a professional, Wall Street-grade Markdown report.
    """
    
    def generate_markdown(self, json_path: str, output_path: str):
        abs_json_path = os.path.abspath(json_path)
        abs_output_path = os.path.abspath(output_path)
        
        with open(abs_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        md = []
        md.append("# Equity Research Report: Earnings Call Analysis\n")
        
        # 1. Executive Summary
        md.append("## Executive Summary")
        md.append(data.get("executive_summary", "No summary provided."))
        md.append("")
        
        # 2. Revenue & Margins
        md.append("## Financial Performance")
        for item in data.get("revenue_and_margins", []):
            md.append(f"- {item}")
        md.append("")
        
        # 3. Regional Performance
        md.append("## Regional Performance")
        for region in data.get("regional_performance", []):
            md.append(f"### {region.get('region_name')}")
            md.append(f"{region.get('performance_summary')}\n")
            
        # 4. Sector Performance
        md.append("## Sector / Vertical Performance")
        for sector in data.get("sector_performance", []):
            md.append(f"### {sector.get('sector_name')}")
            md.append(f"{sector.get('performance_summary')}\n")
            
        # 5. Deal Pipeline
        md.append("## Large Deals & Pipeline")
        for deal in data.get("large_deals_and_pipeline", []):
            md.append(f"- **{deal.get('deal_name_or_client')}** ({deal.get('deal_value')}): {deal.get('details')}")
        md.append("")
            
        # 6. Strategic Initiatives
        md.append("## Strategic Initiatives")
        for item in data.get("strategic_initiatives", []):
            md.append(f"- {item}")
        md.append("")
            
        # 7. Headwinds & Risks
        md.append("## Headwinds & Risks")
        for item in data.get("headwinds_and_risks", []):
            md.append(f"- {item}")
        md.append("")
        
        # 8. Management Guidance
        md.append("## Management Guidance")
        for item in data.get("management_guidance", []):
            md.append(f"- {item}")
        md.append("")
        
        # 9. Q&A Highlights with Sentiment
        md.append("## Q&A Highlights")
        for qa in data.get("q_and_a_highlights", []):
            md.append(f"### Q: {qa.get('analyst_name')}")
            
            # Highlight Evasion
            if qa.get("evasion_flag"):
                md.append("> [!WARNING]")
                md.append("> **Evasion Detected:** Management avoided a direct answer to this question.\n")
                
            md.append(f"**Core Concern:** {qa.get('core_concern')}\n")
            md.append(f"**Management Response:** {qa.get('management_response_summary')}\n")
            md.append(f"**Sentiment Analysis:** {qa.get('sentiment')}\n")
            md.append("---\n")
            
        # Write to file
        os.makedirs(os.path.dirname(abs_output_path), exist_ok=True)
        with open(abs_output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md))
            
        print(f"[*] Generated professional Markdown report at: {abs_output_path}")

