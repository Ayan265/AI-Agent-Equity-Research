import os
import hashlib

class CacheSystem:
    """
    Aggressive Disk Caching Engine.
    Ensures that identical API requests are loaded from disk instead of wasting tokens.
    """
    def __init__(self, cache_dir: str = ".cache/api_responses"):
        self.cache_dir = os.path.abspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _generate_hash(self, prompt: str, schema_name: str) -> str:
        # Hashing the prompt and schema name guarantees we don't load stale data
        hash_input = f"{prompt}_{schema_name}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
        
    def get_cached_response(self, prompt: str, schema_name: str):
        hash_key = self._generate_hash(prompt, schema_name)
        cache_path = os.path.join(self.cache_dir, f"{hash_key}.json")
        
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
        
    def save_to_cache(self, prompt: str, schema_name: str, response_text: str):
        hash_key = self._generate_hash(prompt, schema_name)
        cache_path = os.path.join(self.cache_dir, f"{hash_key}.json")
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(response_text)
