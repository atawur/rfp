import pytest
from app.discovery.candidate_discovery import RFPCandidate
from app.extraction.deterministic_extractor import deterministic_extractor
from app.parsers.jsonld_parser import jsonld_parser
from app.parsers.table_parser import table_parser
from app.parsers.generic_parser import generic_parser
from app.schemas.rfp_classification import ALLOWED_PRIMARY_CATEGORIES, ALLOWED_PROCUREMENT_TYPES

def test_jsonld_parser():
    jsonld_html = """
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "GovernmentService",
            "name": "Endpoint Detection and Response Software Licensing",
            "identifier": "CYBER-EDR-2026",
            "description": "Procurement of 5000 EDR agent licenses with 24/7 SOC integration support.",
            "startDate": "2026-09-01",
            "endDate": "2026-10-31",
            "provider": {
                "@type": "Organization",
                "name": "Department of Homeland Information"
            }
        }
        </script>
    </head>
    <body>
        <h1>Procurement</h1>
    </body>
    </html>
    """
    candidate = RFPCandidate(
        candidate_id="https://dept.gov/edr",
        source_url="https://dept.gov/edr",
        candidate_type="individual_page",
        title="Procurement",
        normalized_content=jsonld_html,
    )
    # Set raw_html attribute for jsonld parser
    candidate.raw_html = jsonld_html

    assert jsonld_parser.can_parse(candidate) is True
    items = jsonld_parser.parse(candidate)
    assert len(items) == 1
    item = items[0]
    assert item.title == "Endpoint Detection and Response Software Licensing"
    assert item.reference_number == "CYBER-EDR-2026"
    assert item.submission_deadline == "2026-10-31"
    assert item.organization == "Department of Homeland Information"

def test_table_parser():
    candidate = RFPCandidate(
        candidate_id="https://bank.com/tenders#row-0-1",
        source_url="https://bank.com/tenders",
        candidate_type="listing_item",
        title="Supply of 200 Core Banking Rack Servers",
        normalized_content="Title: Supply of 200 Core Banking Rack Servers\nReference Number: BK-SRV-2026\nSubmission Deadline: 2026-11-20",
        metadata={
            "reference_number": "BK-SRV-2026",
            "submission_deadline": "2026-11-20",
        },
        document_urls=["https://bank.com/docs/BK-SRV-2026.pdf"],
        raw_row=["Supply of 200 Core Banking Rack Servers", "BK-SRV-2026", "2026-11-20"],
    )

    assert table_parser.can_parse(candidate) is True
    items = table_parser.parse(candidate)
    assert len(items) == 1
    assert items[0].title == "Supply of 200 Core Banking Rack Servers"
    assert items[0].reference_number == "BK-SRV-2026"
    assert items[0].submission_deadline == "2026-11-20"

def test_controlled_category_classification():
    cyber_text = "Tender for 24/7 Security Operations Center (SOC) monitoring and SIEM firewall integration."
    cat, sub, proc, conf, kws, reason = deterministic_extractor.classify_category(cyber_text)
    assert cat == "cybersecurity"
    assert cat in ALLOWED_PRIMARY_CATEGORIES
    assert proc in ALLOWED_PROCUREMENT_TYPES
    assert conf >= 0.70
    assert any(k in ["soc", "siem", "firewall"] for k in kws)

    hardware_text = "Procurement of Cisco core switches, routers, and high capacity rack servers."
    cat2, sub2, proc2, conf2, kws2, reason2 = deterministic_extractor.classify_category(hardware_text)
    assert cat2 == "hardware"
    assert cat2 in ALLOWED_PRIMARY_CATEGORIES
    assert any(k in ["switches", "switch", "router", "routers", "server"] for k in kws2)

def test_high_confidence_deterministic_extraction():
    candidate = RFPCandidate(
        candidate_id="https://example.com/rfp/firewall",
        source_url="https://example.com/rfp/firewall",
        candidate_type="individual_page",
        title="Procurement of Next-Gen Enterprise Firewall and SOC Integration",
        normalized_content=(
            "Title: Procurement of Next-Gen Enterprise Firewall and SOC Integration\n"
            "Reference Number: RFP-2026-FW-889\n"
            "Submission Deadline: 2026-11-15\n"
            "Organization: Central National Bank\n"
            "Description: Central National Bank invites bids for redundant next-generation firewalls with 3 years 24/7 SOC integration support.\n"
            "Contact: procurement@centralbank.org\n"
        ),
        document_urls=["https://example.com/rfp/firewall.pdf"],
    )

    result = deterministic_extractor.extract_candidate(candidate)
    assert result.is_high_confidence is True
    assert result.item.confidence >= 0.80
    assert result.item.primary_category == "cybersecurity"
    assert result.item.reference_number == "RFP-2026-FW-889"
    assert result.item.submission_deadline == "2026-11-15"
    assert result.validation_status == "VALID"
