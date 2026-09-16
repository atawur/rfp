import pytest
from unittest.mock import MagicMock
from app.discovery.candidate_discovery import RFPCandidate
from app.llm_pipeline.llm_queue import LLMQueue, QueueItem
from app.llm_pipeline.llm_cache_service import llm_cache_service
from app.llm_pipeline.batch_processor import BatchProcessor
from app.models.llm_cache import LLMCache

def test_llm_queue():
    queue = LLMQueue()
    assert queue.size == 0

    c1 = RFPCandidate(candidate_id="u1", source_url="u1", candidate_type="individual_page", title="T1", normalized_content="C1")
    c2 = RFPCandidate(candidate_id="u2", source_url="u2", candidate_type="individual_page", title="T2", normalized_content="C2")

    queue.enqueue(QueueItem(candidate=c1, content_hash="hash1", normalized_url="u1"))
    queue.enqueue(QueueItem(candidate=c2, content_hash="hash2", normalized_url="u2"))

    assert queue.size == 2
    items = queue.get_all_items()
    assert len(items) == 2
    assert items[0].content_hash == "hash1"

    queue.clear()
    assert queue.size == 0

def test_llm_cache_storage_and_hit():
    mock_db = MagicMock()
    mock_entry = MagicMock(spec=LLMCache)
    mock_entry.response_json = [{
        "title": "Cached Software Proposal",
        "primary_category": "software",
        "confidence": 0.92,
    }]
    mock_db.query.return_value.filter.return_value.first.return_value = mock_entry

    cached = llm_cache_service.get_cached_result(
        db=mock_db,
        content_hash="test_content_hash_123",
        model_name="gpt-4o",
    )

    assert cached is not None
    assert len(cached) == 1
    assert cached[0]["title"] == "Cached Software Proposal"
    assert cached[0]["primary_category"] == "software"

def test_batch_processor_cache_hit_bypasses_llm():
    mock_db = MagicMock()
    mock_entry = MagicMock(spec=LLMCache)
    mock_entry.response_json = [{
        "title": "Cached RFP Title",
        "primary_category": "cloud",
        "procurement_type": "service",
        "confidence": 0.95,
    }]
    mock_db.query.return_value.filter.return_value.first.return_value = mock_entry

    c1 = RFPCandidate(
        candidate_id="https://test.com/rfp",
        source_url="https://test.com/rfp",
        candidate_type="individual_page",
        title="Uncertain RFP",
        normalized_content="Some content",
    )
    item = QueueItem(candidate=c1, content_hash="hash_abc", normalized_url="https://test.com/rfp")

    processor = BatchProcessor(batch_size=5)
    mock_metrics = MagicMock()

    results = processor.process_queue(db=mock_db, queue_items=[item], metrics=mock_metrics)

    assert len(results) == 1
    assert results[0]["title"] == "Cached RFP Title"
    assert results[0]["extraction_method"] == "llm_cache"
    mock_metrics.record_cache_hit.assert_called_once()
    mock_metrics.record_llm_call.assert_not_called()
