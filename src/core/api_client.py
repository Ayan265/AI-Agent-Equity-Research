import os
from dotenv import load_dotenv
import litellm
import google.generativeai as genai
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from core.cache_system import CacheSystem

load_dotenv()

class RateLimitError(Exception):
    pass

class HardQuotaError(Exception):
    pass

class APIClient:
    """
    A centralized, bulletproof API router.
    Handles rate limiting, multi-model fallbacks, and aggressive caching.
    """
    def __init__(self):
        # The Fallback Chain: AI will try these in order until one succeeds
        self.fallback_chain = [
            "openrouter/anthropic/claude-3.5-sonnet-20240620",
            "openrouter/openai/gpt-4o",
            "gemini/gemini-3.5-flash",
            "openrouter/meta-llama/llama-3.1-70b-instruct",
            "openrouter/meta-llama/llama-3.1-8b-instruct:free"
        ]
        self.cache = CacheSystem()
        
    @retry(
        wait=wait_exponential(multiplier=2, min=10, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(RateLimitError),
        reraise=True
    )
    def _make_api_call_with_retry(self, prompt: str, schema_class, target_model: str) -> str:
        try:
            if target_model.startswith("gemini/"):
                genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
                google_model_name = target_model.split("/")[1]
                genai_model = genai.GenerativeModel(google_model_name)
                
                if schema_class:
                    system_instruction = "You are a Senior Equity Research Analyst. Return strictly JSON data that matches the requested schema."
                    full_prompt = f"{system_instruction}\n\nSchema:\n{schema_class.model_json_schema()}\n\n{prompt}"
                    response = genai_model.generate_content(
                        full_prompt,
                        generation_config=genai.GenerationConfig(
                            response_mime_type="application/json",
                            temperature=0.1
                        )
                    )
                else:
                    system_instruction = "You are a Senior Equity Research Analyst."
                    full_prompt = f"{system_instruction}\n\n{prompt}"
                    response = genai_model.generate_content(full_prompt)
                    
                return response.text
            else:
                if not os.environ.get("OPENROUTER_API_KEY"):
                    raise HardQuotaError(f"Missing API Key for {target_model}")
                    
                messages = [
                    {"role": "system", "content": "You are a highly analytical Senior Equity Research Analyst."},
                    {"role": "user", "content": prompt}
                ]
                
                if schema_class:
                    response = litellm.completion(
                        model=target_model,
                        messages=messages,
                        response_format=schema_class,
                        temperature=0.1
                    )
                else:
                    response = litellm.completion(
                        model=target_model,
                        messages=messages,
                        temperature=0.7
                    )
                return response.choices[0].message.content
                
        except Exception as e:
            error_str = str(e).lower()
            if "hard limit" in error_str:
                print(f"    [!] HARD QUOTA hit for {target_model}. Moving to fallback model.")
                raise HardQuotaError(str(e))
            elif "429" in error_str or "quota" in error_str or "rate limit" in error_str or "free_tier_requests" in error_str:
                print(f"    [!] Rate Limit hit for {target_model}. Pausing and retrying...")
                raise RateLimitError(str(e))
            else:
                raise e

    def extract_structured_json(self, prompt: str, schema_class, model: str = None) -> str:
        schema_name = schema_class.__name__ if schema_class else "RawText"
        
        # Check Cache First!
        cached_response = self.cache.get_cached_response(prompt, schema_name)
        if cached_response:
            print(f"    [✔] Loaded from Cache (0 tokens spent)")
            return cached_response
            
        models_to_try = [model] if model else list(self.fallback_chain)
        
        for target_model in models_to_try:
            # If a previous step pruned it from the global chain, we might still want to skip it, 
            # but models_to_try handles the current run. We'll check if it's still in the fallback chain 
            # to ensure we don't try models that were pruned in a parallel or earlier context.
            if not model and target_model not in self.fallback_chain:
                continue

            print(f"[*] Routing request to {target_model}...")
            try:
                # Attempt call (handles soft rate limits automatically via @retry)
                response_text = self._make_api_call_with_retry(prompt, schema_class, target_model)
                
                # If successful, save to cache and return
                self.cache.save_to_cache(prompt, schema_name, response_text)
                return response_text
                
            except HardQuotaError:
                print(f"    [!] Pruning {target_model} from active chain due to Hard Quota.")
                if target_model in self.fallback_chain:
                    self.fallback_chain.remove(target_model)
                continue
            except Exception as e:
                error_str = str(e).lower()
                print(f"    [X] Unexpected error with {target_model}: {e}")
                
                # Prune models that are out of credits (402) or not found (404)
                if "402" in error_str or "credits" in error_str or "404" in error_str or "not found" in error_str:
                    print(f"    [!] Pruning {target_model} from active chain due to fatal API error.")
                    if target_model in self.fallback_chain:
                        self.fallback_chain.remove(target_model)
                continue
                
        # If we exhausted all models in the fallback chain
        raise Exception("All models in the fallback chain failed or hit hard quotas.")
