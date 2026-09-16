import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class PipelineMetrics:
    total_websites: int = 0
    successful_scrapes: int = 0
    failed_scrapes: int = 0

    rfp_candidates: int = 0
    unchanged_rfps: int = 0
    new_rfps: int = 0
    changed_rfps: int = 0

    deterministic_extractions: int = 0
    llm_queue_size: int = 0
    llm_extractions: int = 0

    llm_calls: int = 0
    llm_cache_hits: int = 0

    validation_failures: int = 0
    extraction_failures: int = 0

    input_tokens: int = 0
    output_tokens: int = 0
    start_time: float = field(default_factory=time.time)

    def record_scrape(self, success: bool):
        if success:
            self.successful_scrapes += 1
        else:
            self.failed_scrapes += 1

    def record_candidate(self, status: str):
        self.rfp_candidates += 1
        if status == "UNCHANGED":
            self.unchanged_rfps += 1
        elif status == "NEW":
            self.new_rfps += 1
        elif status == "CHANGED":
            self.changed_rfps += 1

    def record_deterministic(self):
        self.deterministic_extractions += 1

    def record_llm_queue(self):
        self.llm_queue_size += 1

    def record_llm_call(self, count: int = 1):
        self.llm_calls += count

    def record_cache_hit(self):
        self.llm_cache_hits += 1

    def record_validation_failure(self):
        self.validation_failures += 1

    def record_extraction_failure(self):
        self.extraction_failures += 1

    def to_dict(self) -> Dict[str, Any]:
        duration = round(time.time() - self.start_time, 2)
        return {
            "total_websites": self.total_websites,
            "successful_scrapes": self.successful_scrapes,
            "failed_scrapes": self.failed_scrapes,
            "rfp_candidates": self.rfp_candidates,
            "unchanged_rfps": self.unchanged_rfps,
            "new_rfps": self.new_rfps,
            "changed_rfps": self.changed_rfps,
            "deterministic_extractions": self.deterministic_extractions,
            "llm_queue_size": self.llm_queue_size,
            "llm_extractions": self.llm_extractions,
            "llm_calls": self.llm_calls,
            "llm_cache_hits": self.llm_cache_hits,
            "validation_failures": self.validation_failures,
            "extraction_failures": self.extraction_failures,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "duration_seconds": duration,
        }

    def summary_report(self) -> str:
        d = self.to_dict()
        report = (
            f"\n==================== RFP PIPELINE RUN REPORT ====================\n"
            f"Websites: {d['total_websites']}\n"
            f"  Successful: {d['successful_scrapes']}\n"
            f"  Failed: {d['failed_scrapes']}\n\n"
            f"RFP candidates: {d['rfp_candidates']}\n"
            f"  Unchanged (Skipped): {d['unchanged_rfps']}\n"
            f"  New: {d['new_rfps']}\n"
            f"  Changed: {d['changed_rfps']}\n\n"
            f"Extraction breakdown:\n"
            f"  Deterministic (Zero LLM calls): {d['deterministic_extractions']}\n"
            f"  LLM queue size: {d['llm_queue_size']}\n"
            f"  LLM extractions: {d['llm_extractions']}\n\n"
            f"LLM performance & caching:\n"
            f"  LLM API calls: {d['llm_calls']}\n"
            f"  LLM Cache hits: {d['llm_cache_hits']}\n\n"
            f"Quality & Resilience:\n"
            f"  Validation failures: {d['validation_failures']}\n"
            f"  Extraction failures: {d['extraction_failures']}\n"
            f"  Duration: {d['duration_seconds']}s\n"
            f"=================================================================="
        )
        return report
