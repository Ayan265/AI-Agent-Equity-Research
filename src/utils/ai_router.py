import os
from dotenv import load_dotenv
import litellm
import json
import google.generativeai as genai

# Load environment variables (API Keys)
load_dotenv()

class AIRouter:
    def __init__(self, primary_model: str = "gemini/gemini-3.5-flash"):
        self.primary_model = primary_model

    def extract_structured_json(self, prompt: str, schema_class, model: str = None) -> str:
        target_model = model if model else self.primary_model
        print(f"[*] Routing request to {target_model}...")

        try:
            if target_model.startswith("gemini/"):
                # Use official Google SDK for maximum compatibility
                genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
                google_model_name = target_model.split("/")[1]
                
                # Gemini 1.5 models support structured outputs directly
                genai_model = genai.GenerativeModel(google_model_name)
                
                # We format the schema manually for Google's API to ensure 100% compatibility
                system_instruction = "You are a Senior Equity Research Analyst. Return strictly JSON data that matches the requested schema."
                full_prompt = f"{system_instruction}\n\nSchema:\n{schema_class.model_json_schema()}\n\n{prompt}"
                
                response = genai_model.generate_content(
                    full_prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )
                return response.text
            else:
                # Use LiteLLM for OpenRouter, Kimi, OpenAI, Anthropic
                response = litellm.completion(
                    model=target_model,
                    messages=[
                        {"role": "system", "content": "You are a highly analytical Senior Equity Research Analyst. Extract the requested data accurately."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format=schema_class,
                    temperature=0.1
                )
                return response.choices[0].message.content

        except Exception as e:
            print(f"[!] API Error routing to {target_model}: {e}")
            raise e
