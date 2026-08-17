from pydantic import BaseModel, Field
from typing import List
from core.api_client import APIClient
import json

class QuestionAndAnswer(BaseModel):
    question: str = Field(description="The specific question or sub-question asked by the analyst.")
    direct_answer: str = Field(description="The precise and concise answer given by management to this specific question.")

class AnalystInteraction(BaseModel):
    analyst_name: str = Field(description="The name of the analyst.")
    firm: str = Field(description="The firm the analyst represents (e.g., Axis Capital, Equirus Securities). If not mentioned, return 'Unknown'.")
    qa_pairs: List[QuestionAndAnswer] = Field(description="A list of all the specific questions asked and the answers provided during this interaction.")

class QADeepExtractor:
    def __init__(self):
        self.router = APIClient()

    def analyze_qa_session(self, analyst_name: str, discussion_text: str) -> dict:
        prompt = f"""
        You are an elite Dalal Street Quantitative Researcher.
        Read this specific Q&A interaction between Analyst {analyst_name} and Management.
        Analysts often ask multiple sub-questions in one breath.
        Break down the interaction into individual Question and Answer pairs.
        Extract the exact question asked, and the direct answer given. Keep the answers concise and highly informative.
        
        Interaction:
        {discussion_text}
        """
        
        json_result = self.router.extract_structured_json(prompt, schema_class=AnalystInteraction)
        return json.loads(json_result)
