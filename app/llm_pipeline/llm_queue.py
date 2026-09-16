import logging
from dataclasses import dataclass
from typing import List, Optional, Any
from app.discovery.candidate_discovery import RFPCandidate
from app.parsers.base import ParsedRFPItem

logger = logging.getLogger(__name__)

@dataclass
class QueueItem:
    candidate: RFPCandidate
    content_hash: str
    normalized_url: str
    website_id: Optional[int] = None
    initial_deterministic: Optional[ParsedRFPItem] = None

class LLMQueue:
    """
    Queue layer that aggregates candidates requiring semantic LLM processing.
    Decouples the main website scraping loop from LLM API calls.
    """

    def __init__(self):
        self._items: List[QueueItem] = []

    def enqueue(self, item: QueueItem):
        self._items.append(item)
        logger.info(
            f"[LLMQueue] Enqueued candidate '{item.candidate.title[:30]}...' "
            f"(queue size: {len(self._items)})"
        )

    def get_all_items(self) -> List[QueueItem]:
        return list(self._items)

    def clear(self):
        self._items.clear()

    @property
    def size(self) -> int:
        return len(self._items)

llm_queue = LLMQueue()
