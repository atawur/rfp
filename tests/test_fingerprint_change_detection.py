import pytest
from app.fingerprint.hasher import content_fingerprinter
from app.discovery.candidate_discovery import candidate_discovery_service
from app.normalization.normalizer import generic_normalizer

HTML_RUN_1 = """
<html>
<body>
    <div id="session-info">Session ID: 93847294872 | Page generated: 2026-09-16 10:00:00</div>
    <main>
        <h1>Supply and Delivery of 100 Laptops</h1>
        <p>Reference: RFP-2026-LAPTOP-01</p>
        <p>Deadline: 2026-10-15</p>
        <p>Estimated Budget: $120,000</p>
    </main>
</body>
</html>
"""

HTML_RUN_2_SAME_CONTENT_DIFFERENT_NOISE = """
<html>
<body>
    <div id="session-info">Session ID: abc998811223 | Page generated: 2026-09-16 14:30:15</div>
    <div class="ad-banner">Super Sale Ad</div>
    <main>
        <h1>Supply and Delivery of 100 Laptops</h1>
        <p>Reference: RFP-2026-LAPTOP-01</p>
        <p>Deadline: 2026-10-15</p>
        <p>Estimated Budget: $120,000</p>
    </main>
</body>
</html>
"""

HTML_RUN_3_DEADLINE_CHANGED = """
<html>
<body>
    <main>
        <h1>Supply and Delivery of 100 Laptops</h1>
        <p>Reference: RFP-2026-LAPTOP-01</p>
        <p>Deadline: 2026-10-30</p>
        <p>Estimated Budget: $120,000</p>
    </main>
</body>
</html>
"""

def test_identical_content_hash():
    doc1 = generic_normalizer.normalize(HTML_RUN_1, "https://example.com/rfp-laptop")
    hash1 = content_fingerprinter.compute_hash(doc1.raw_relevant_text)

    # Even with different session IDs, timestamps, and ad banners, hash MUST be identical
    doc2 = generic_normalizer.normalize(HTML_RUN_2_SAME_CONTENT_DIFFERENT_NOISE, "https://example.com/rfp-laptop")
    hash2 = content_fingerprinter.compute_hash(doc2.raw_relevant_text)

    assert hash1 == hash2, "Meaningful RFP content is identical; hash must match!"

def test_deadline_change_detects_difference():
    doc1 = generic_normalizer.normalize(HTML_RUN_1, "https://example.com/rfp-laptop")
    hash1 = content_fingerprinter.compute_hash(doc1.raw_relevant_text)

    doc3 = generic_normalizer.normalize(HTML_RUN_3_DEADLINE_CHANGED, "https://example.com/rfp-laptop")
    hash3 = content_fingerprinter.compute_hash(doc3.raw_relevant_text)

    assert hash1 != hash3, "Deadline changed; content hash must differ to trigger re-extraction!"

def test_url_normalization_strips_tracking():
    raw_url1 = "https://example.com/tenders/rfp-123?utm_source=google&utm_medium=cpc&sessionid=999"
    raw_url2 = "https://example.com/tenders/rfp-123?utm_medium=cpc&utm_source=google"
    raw_url3 = "HTTPS://EXAMPLE.COM/tenders/rfp-123"

    norm1 = content_fingerprinter.normalize_url(raw_url1)
    norm2 = content_fingerprinter.normalize_url(raw_url2)
    norm3 = content_fingerprinter.normalize_url(raw_url3)

    assert norm1 == norm2 == norm3 == "https://example.com/tenders/rfp-123"

def test_rfp_level_candidate_discovery_on_tables():
    html_listing = """
    <html>
    <body>
        <h1>Active Procurement Opportunities</h1>
        <table>
            <tr><th>Tender Title</th><th>Ref No</th><th>Submission Deadline</th></tr>
            <tr><td>Network Security Firewall Upgrade</td><td>FW-2026</td><td>2026-10-10</td></tr>
            <tr><td>Cloud Migration Consultancy</td><td>CLOUD-01</td><td>2026-11-01</td></tr>
            <tr><td>Civil Work Office Renovation</td><td>CIV-88</td><td>2026-12-15</td></tr>
        </table>
    </body>
    </html>
    """
    doc = generic_normalizer.normalize(html_listing, "https://example.com/listing")
    candidates = candidate_discovery_service.discover_candidates(doc)

    assert len(candidates) == 3
    assert candidates[0].title == "Network Security Firewall Upgrade"
    assert candidates[1].title == "Cloud Migration Consultancy"
    assert candidates[2].title == "Civil Work Office Renovation"

    # Each individual candidate has its own unique hash
    hashes = [content_fingerprinter.compute_hash(c.normalized_content) for c in candidates]
    assert len(set(hashes)) == 3, "Each RFP candidate must produce a distinct hash for independent change tracking"
