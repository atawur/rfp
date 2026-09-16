import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
import app.db.base  # Register all SQLAlchemy models
from app.db.session import SessionLocal
from app.services.rfp_service import rfp_service
from app.metrics.pipeline_metrics import PipelineMetrics
from app.models.website import Website


SAMPLE_HTML_PORTAL = """
<!DOCTYPE html>
<html>
<head>
    <title>National Highway Authority - Tender Portal</title>
</head>
<body>
    <main>
        <h1>Supply and Commissioning of Intelligent Traffic Surveillance System {slug}</h1>
        <p>Reference: NHA-CCTV-{slug}</p>
        <p>Deadline: 2026-11-30</p>
        <p>Description: The National Highway Authority invites sealed bids for supply, installation, and commissioning of IP CCTV cameras, NVRs, and video management software across 12 toll plazas.</p>
        <p>Contact: tender@nha.gov.pk</p>
        <a href="https://nha.gov.pk/docs/tender_cctv.pdf">Download Tender Document</a>
    </main>
</body>
</html>
"""

import uuid

def test_pipeline_e2e_deterministic_and_change_detection():
    db = SessionLocal()
    unique_slug = uuid.uuid4().hex[:8]
    test_url = f"https://nha.gov.pk/tenders/cctv-{unique_slug}"
    html_content = SAMPLE_HTML_PORTAL.format(slug=unique_slug)
    try:
        metrics = PipelineMetrics(total_websites=1)

        # Mock playwright to return html_content
        with patch("app.crawler.playwright_crawler.playwright_crawler.fetch_page_content", return_value=html_content):
            # Run 1: First time URL is crawled
            results_run1 = rfp_service.extract_and_process_url(
                db=db,
                url=test_url,
                notify=False,
                metrics=metrics,
            )

            assert len(results_run1) >= 1
            inserted = [r for r in results_run1 if r.get("status") in ["inserted", "updated"]]
            assert len(inserted) >= 1
            assert "Intelligent Traffic Surveillance" in inserted[0]["title"]
            # Should have extracted deterministically with 0 LLM calls!
            assert metrics.llm_calls == 0
            assert metrics.deterministic_extractions >= 1

            # Run 2: Exact same page crawled again (e.g. daily crawl next day)
            metrics_run2 = PipelineMetrics(total_websites=1)
            results_run2 = rfp_service.extract_and_process_url(
                db=db,
                url=test_url,
                notify=False,
                metrics=metrics_run2,
            )

            # Expected: UNCHANGED -> SKIP -> 0 LLM calls
            assert len(results_run2) >= 1
            ignored = [r for r in results_run2 if r.get("status") == "ignored"]
            assert len(ignored) >= 1
            assert "unchanged content" in ignored[0]["reason"]
            assert metrics_run2.llm_calls == 0
            assert metrics_run2.unchanged_rfps >= 1

            # Verify metrics report format
            report = metrics_run2.summary_report()
            assert "RFP PIPELINE RUN REPORT" in report
            assert "Unchanged (Skipped): 1" in report

    finally:
        db.close()
