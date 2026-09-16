import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.llm_pipeline.llm_queue import QueueItem
from app.llm_pipeline.llm_cache_service import llm_cache_service
from app.validation.validator import unified_validator
from app.services.agent_config_service import agent_config_service

logger = logging.getLogger(__name__)

class BatchProcessor:
    """
    Processes queued RFP candidates in configurable batches.
    Checks persistent LLM cache first, formats compact token-minimized payloads,
    and invokes the active AI agent.
    """

    def __init__(self, batch_size: int = 8):
        self.batch_size = batch_size

    def process_queue(
        self,
        db: Session,
        queue_items: List[QueueItem],
        metrics: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        if not queue_items:
            return []

        active_config = None
        try:
            active_config = agent_config_service.get_active_config(db)
        except Exception:
            pass
        model_name = getattr(active_config, "model_name", "gpt-4o") or "gpt-4o"

        final_extracted: List[Dict[str, Any]] = []
        uncached_items: List[QueueItem] = []

        # 1. Check persistent LLM Cache for each queue item
        for item in queue_items:
            cached = llm_cache_service.get_cached_result(db, item.content_hash, model_name)
            if cached:
                if metrics:
                    metrics.record_cache_hit()
                logger.info(f"[BatchProcessor] Reused {len(cached)} cached RFP(s) for {item.normalized_url}")
                for rfp_dict in cached:
                    rfp_dict["source_url"] = item.candidate.source_url
                    rfp_dict["website_id"] = item.website_id
                    rfp_dict["content_hash"] = item.content_hash
                    rfp_dict["extraction_method"] = "llm_cache"
                    final_extracted.append(rfp_dict)
            else:
                uncached_items.append(item)

        if not uncached_items:
            logger.info("[BatchProcessor] All queued items resolved via cache. 0 LLM calls needed.")
            return final_extracted

        agent = agent_config_service.get_active_agent(db)
        model_name = getattr(agent, "model", model_name)


        # 2. Slice uncached items into manageable batches
        batches = [
            uncached_items[i : i + self.batch_size]
            for i in range(0, len(uncached_items), self.batch_size)
        ]

        logger.info(f"[BatchProcessor] Processing {len(uncached_items)} items in {len(batches)} batch(es).")

        for batch_idx, batch in enumerate(batches, start=1):
            if metrics:
                metrics.record_llm_call()

            # Format compact combined prompt
            batch_texts = []
            for idx, item in enumerate(batch, start=1):
                clean_snippet = item.candidate.normalized_content[:3000]
                batch_texts.append(
                    f"--- ITEM {idx} ---\n"
                    f"URL: {item.candidate.source_url}\n"
                    f"Title: {item.candidate.title}\n"
                    f"Content:\n{clean_snippet}\n"
                )
            combined_content = "\n".join(batch_texts)

            try:
                # Use agent to extract structured items
                extracted_batch = agent.run(
                    url=batch[0].candidate.source_url,
                    initial_content=combined_content
                )

                # Store each extracted result in cache
                for idx, item in enumerate(batch):
                    matched_results = [
                        res for res in extracted_batch
                        if (
                            res.get("source_url") == item.candidate.source_url or
                            item.candidate.title.lower() in str(res.get("title", "")).lower() or
                            str(res.get("title", "")).lower() in item.candidate.title.lower()
                        )
                    ]

                    results_to_save = matched_results if matched_results else (
                        [extracted_batch[idx]] if idx < len(extracted_batch) else []
                    )

                    if not results_to_save and item.initial_deterministic:
                        # Fallback to deterministic item if LLM missed this specific item in the batch
                        logger.warning(f"Item {item.candidate.title} omitted by LLM; falling back to deterministic.")
                        results_to_save = [item.initial_deterministic.to_dict()]

                    for rfp_dict in results_to_save:
                        rfp_dict["source_url"] = item.candidate.source_url
                        rfp_dict["website_id"] = item.website_id
                        rfp_dict["content_hash"] = item.content_hash
                        rfp_dict["extraction_method"] = "llm"
                        final_extracted.append(rfp_dict)

                    if results_to_save:
                        llm_cache_service.store_cached_result(
                            db=db,
                            content_hash=item.content_hash,
                            model_name=model_name,
                            response_data=results_to_save,
                        )

            except Exception as batch_err:
                logger.error(f"[BatchProcessor] Batch {batch_idx} failed: {batch_err}. Using deterministic fallback.")
                if metrics:
                    metrics.record_extraction_failure()
                # Resilient fallback: use deterministic results for each item in the failed batch
                for item in batch:
                    if item.initial_deterministic:
                        rfp_dict = item.initial_deterministic.to_dict()
                        rfp_dict["source_url"] = item.candidate.source_url
                        rfp_dict["website_id"] = item.website_id
                        rfp_dict["content_hash"] = item.content_hash
                        rfp_dict["extraction_method"] = "deterministic_fallback"
                        final_extracted.append(rfp_dict)

        return final_extracted

batch_processor = BatchProcessor()
