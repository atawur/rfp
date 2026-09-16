import hashlib
import json
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.llm_cache import LLMCache

logger = logging.getLogger(__name__)

PROMPT_VERSION = 1
SCHEMA_VERSION = 1

class LLMCacheService:
    """
    Manages persistent caching of LLM extraction results based on:
    content_hash + prompt_version + schema_version + model_name.
    Avoids duplicate LLM API calls and token charges.
    """

    @staticmethod
    def generate_cache_key(
        content_hash: str,
        model_name: str,
        prompt_version: int = PROMPT_VERSION,
        schema_version: int = SCHEMA_VERSION
    ) -> str:
        raw_key = f"{content_hash}:{prompt_version}:{schema_version}:{model_name.lower().strip()}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def get_cached_result(
        self,
        db: Session,
        content_hash: str,
        model_name: str,
        prompt_version: int = PROMPT_VERSION,
        schema_version: int = SCHEMA_VERSION
    ) -> Optional[List[Dict[str, Any]]]:
        cache_key = self.generate_cache_key(content_hash, model_name, prompt_version, schema_version)
        entry = db.query(LLMCache).filter(LLMCache.cache_key == cache_key).first()
        if entry:
            logger.info(f"[LLMCache] Cache HIT for key {cache_key[:8]} (hash={content_hash[:8]}). 0 tokens used.")
            if isinstance(entry.response_json, list):
                return entry.response_json
            elif isinstance(entry.response_json, dict) and "rfps" in entry.response_json:
                return entry.response_json["rfps"]
            elif isinstance(entry.response_json, dict):
                return [entry.response_json]
        return None

    def store_cached_result(
        self,
        db: Session,
        content_hash: str,
        model_name: str,
        response_data: Any,
        input_tokens: int = 0,
        output_tokens: int = 0,
        prompt_version: int = PROMPT_VERSION,
        schema_version: int = SCHEMA_VERSION
    ) -> LLMCache:
        cache_key = self.generate_cache_key(content_hash, model_name, prompt_version, schema_version)
        entry = db.query(LLMCache).filter(LLMCache.cache_key == cache_key).first()

        if entry:
            entry.response_json = response_data
            entry.input_tokens = input_tokens
            entry.output_tokens = output_tokens
            db.commit()
            return entry
        else:
            new_entry = LLMCache(
                cache_key=cache_key,
                content_hash=content_hash,
                prompt_version=prompt_version,
                schema_version=schema_version,
                model_name=model_name,
                response_json=response_data,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            db.add(new_entry)
            db.commit()
            logger.info(f"[LLMCache] Stored cache entry {cache_key[:8]} for model {model_name}")
            return new_entry

llm_cache_service = LLMCacheService()
