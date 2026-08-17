from pydantic import BaseModel, Field
from typing import List, Optional
from core.api_client import APIClient
import json
import os

# ---------------------------------------------------------
# Phase 1: Opening Remarks Schema
# ---------------------------------------------------------
class RegionalPerformance(BaseModel):
    region_name: str = Field(description="Name of the region (e.g., Americas 1, Americas 2, Europe, APMEA)")
    performance_summary: str = Field(description="Highly detailed summary of revenue, growth, and headwinds in this region.")

class SectorPerformance(BaseModel):
    sector_name: str = Field(description="Name of the vertical (e.g., BFSI, Healthcare, Consumer, Technology)")
    performance_summary: str = Field(description="Highly detailed summary of growth, client behavior, and pipeline in this sector.")

class LargeDeal(BaseModel):
    deal_name_or_client: str = Field(description="Name of the client or deal (e.g., Olam Group)")
    deal_value: str = Field(description="Total contract value or committed spend")
    details: str = Field(description="Why this deal is significant and what services are provided")

class OpeningRemarksAnalysis(BaseModel):
    executive_summary: str = Field(description="A highly detailed 2-3 paragraph summary of the opening remarks, focusing on the most critical takeaways for an institutional investor.")
    revenue_and_margins: List[str] = Field(description="List of all specific revenue, margin, and EPS numbers discussed.")
    regional_performance: List[RegionalPerformance]
    sector_performance: List[SectorPerformance]
    large_deals_and_pipeline: List[LargeDeal]
    strategic_initiatives: List[str] = Field(description="Key strategic shifts (e.g., AI integration, restructuring, consulting turnaround)")
    headwinds_and_risks: List[str] = Field(description="Specific macro or client-level risks mentioned that could hurt future performance")
    management_guidance: List[str] = Field(description="Specific forward-looking guidance given for the next quarter or year.")

# ---------------------------------------------------------
# Phase 2: Q&A Sentiment Schema
# ---------------------------------------------------------
class QAAnalysis(BaseModel):
    analyst_name: str = Field(description="Name of the analyst asking the question")
    core_concern: str = Field(description="What was the analyst fundamentally worried about or asking? Be highly specific.")
    management_response_summary: str = Field(description="How did management answer? Detail their exact logic.")
    sentiment: str = Field(description="The tone of management's response. E.g., 'Defensive', 'Confident', 'Cautious', 'Optimistic'.")
    evasion_flag: bool = Field(description="Set to true if management avoided giving a direct answer to a specific mathematical or qualitative question.")

# ---------------------------------------------------------
# Analyzer Class (Map-Reduce)
# ---------------------------------------------------------
class AIAnalyzer:
    def __init__(self, model_override: str = None):
        self.router = APIClient()

    def analyze_chunks(self, structured_chunks: dict) -> str:
        """
        Runs the Map-Reduce extraction.
        1. Analyzes Opening Remarks.
        2. Analyzes each Analyst Q&A chunk individually for sentiment.
        """
        print("[*] Map-Reduce Phase 1: Analyzing Opening Remarks...")
        opening_prompt = f"""
        You are an elite Dalal Street Quantitative Researcher.
        Analyze the following Opening Remarks from an earnings call transcript.
        Extract the exact data into the requested JSON schema. Focus heavily on Regional Performance, Sector Performance, and Deal Pipelines.
        
        Opening Remarks:
        {structured_chunks['opening_remarks']}
        """
        opening_json = self.router.extract_structured_json(opening_prompt, schema_class=OpeningRemarksAnalysis)
        final_report = json.loads(opening_json)
        
        print(f"[*] Map-Reduce Phase 2: Analyzing {len(structured_chunks['qa_sessions'])} Q&A Sessions for Sentiment...")
        qa_analyses = []
        for i, qa in enumerate(structured_chunks['qa_sessions']):
            analyst = qa["analyst"]
            print(f"    -> Analyzing Q&A for {analyst} ({i+1}/{len(structured_chunks['qa_sessions'])})")
            
            qa_prompt = f"""
            You are an elite Dalal Street Quantitative Researcher.
            Analyze this specific Q&A interaction between Analyst {analyst} and Management.
            Determine the core concern, summarize the response, and aggressively analyze the SENTIMENT and EVASION.
            If management did not answer a direct question, set evasion_flag to true.
            
            Interaction:
            {qa['discussion']}
            """
            
            try:
                qa_result = self.router.extract_structured_json(qa_prompt, schema_class=QAAnalysis)
                qa_analyses.append(json.loads(qa_result))
            except Exception as e:
                print(f"    [!] Failed to analyze {analyst}: {e}")
                
        final_report["q_and_a_highlights"] = qa_analyses
        return json.dumps(final_report, indent=2)

    def save_analysis(self, json_string: str, output_path: str):
        abs_output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_output_path), exist_ok=True)
        
        data = json.loads(json_string)
        with open(abs_output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        print(f"[*] Saved deep AI JSON analysis to: {abs_output_path}")
