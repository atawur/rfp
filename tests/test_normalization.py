import pytest
from app.normalization.normalizer import generic_normalizer

HTML_FIXTURE_STANDARD = """
<!DOCTYPE html>
<html>
<head>
    <title>Global Logistics - IT Procurement Portal</title>
    <meta property="og:title" content="OG Procurement Portal" />
    <script src="https://analytics.com/gtm.js"></script>
    <style>.banner { color: red; }</style>
</head>
<body>
    <header>
        <div class="top-nav">Navigation Menu</div>
    </header>
    <div class="cookie-consent">Please accept cookies.</div>
    <main>
        <h1>Supply of High Performance Workstations</h1>
        <p>Global Logistics Corporation invites sealed bids from eligible vendors.</p>
        <table>
            <tr><th>Tender Ref</th><th>Submission Deadline</th></tr>
            <tr><td>GLC-HW-2026-09</td><td>2026-10-30</td></tr>
        </table>
        <p>For more details, download the specification below.</p>
        <a href="/docs/workstations_specs.pdf">Download Tender Document (PDF)</a>
        <a href="https://example.com/rfp/faq">Procurement FAQ</a>
    </main>
    <div class="ad-banner">Sponsored Ad</div>
    <footer>Copyright 2026 Global Logistics</footer>
</body>
</html>
"""

HTML_FIXTURE_NO_TITLE_TAG = """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:title" content="Bank Central - Core Infrastructure Upgrade" />
</head>
<body>
    <div class="content">
        <h1>Core Network Switch Replacement</h1>
        <p>Request for quotation for 50 enterprise 48-port PoE switches.</p>
        <a href="/tenders/switch_rfq.docx">Download RFQ Notice</a>
    </div>
</body>
</html>
"""

HTML_FIXTURE_ONLY_OG_TITLE = """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:title" content="Municipal Water Dept - SCADA Security Audit" />
</head>
<body>
    <article>
        <h2>Cybersecurity Assessment for SCADA Network</h2>
        <p>Audit and penetration testing required for water distribution control systems.</p>
    </article>
</body>
</html>
"""

def test_title_fallback_hierarchy():
    # 1. Standard HTML with <title> tag
    doc1 = generic_normalizer.normalize(HTML_FIXTURE_STANDARD, source_url="https://globallogistics.com/tenders")
    assert doc1.page.title == "Global Logistics - IT Procurement Portal"

    # 2. HTML without <title> tag falls back to <h1>
    doc2 = generic_normalizer.normalize(HTML_FIXTURE_NO_TITLE_TAG, source_url="https://bankcentral.com/procurement")
    assert doc2.page.title == "Core Network Switch Replacement"

    # 3. HTML without <title> and without <h1> falls back to og:title
    doc3 = generic_normalizer.normalize(HTML_FIXTURE_ONLY_OG_TITLE, source_url="https://waterdept.gov/rfp")
    assert doc3.page.title == "Municipal Water Dept - SCADA Security Audit"

def test_noise_cleaning():
    doc = generic_normalizer.normalize(HTML_FIXTURE_STANDARD, source_url="https://globallogistics.com/tenders")
    clean_text = doc.raw_relevant_text

    # Scripts, ads, and cookie banners should be stripped
    assert "gtm.js" not in clean_text
    assert "Please accept cookies" not in clean_text
    assert "Sponsored Ad" not in clean_text
    assert "Navigation Menu" not in clean_text

    # Semantic content should be preserved
    assert "Supply of High Performance Workstations" in clean_text
    assert "GLC-HW-2026-09" in clean_text
    assert "2026-10-30" in clean_text

def test_link_extraction_and_url_normalization():
    doc = generic_normalizer.normalize(HTML_FIXTURE_STANDARD, source_url="https://globallogistics.com/tenders")
    assert len(doc.links) >= 2

    # Check relative URL resolved to absolute
    pdf_link = next(l for l in doc.links if l.type == "pdf")
    assert pdf_link.url == "https://globallogistics.com/docs/workstations_specs.pdf"
    assert pdf_link.type == "pdf"
    assert pdf_link.is_rfp_signal is True

    # Check HTML link with RFP keyword
    faq_link = next(l for l in doc.links if "faq" in l.url)
    assert faq_link.url == "https://example.com/rfp/faq"
    assert faq_link.type == "html"
    assert faq_link.is_rfp_signal is True

def test_table_content_extraction():
    doc = generic_normalizer.normalize(HTML_FIXTURE_STANDARD, source_url="https://globallogistics.com/tenders")
    assert len(doc.page.tables) == 1
    table = doc.page.tables[0]
    assert table[0] == ["Tender Ref", "Submission Deadline"]
    assert table[1] == ["GLC-HW-2026-09", "2026-10-30"]
