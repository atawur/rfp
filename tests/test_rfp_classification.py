import json
from unittest.mock import MagicMock, patch
import pytest
from pydantic import ValidationError

import app.db.base  # Register all SQLAlchemy models
from app.schemas.rfp_classification import (
    ALLOWED_PRIMARY_CATEGORIES,
    ALLOWED_PROCUREMENT_TYPES,
    RFPClassificationResult,
)
from app.services.rfp_classification_service import RFPClassificationService
from app.services.rfp_service import RFPService


# =====================================================================
# 1. Validation & Schema Tests
# =====================================================================

def test_valid_rfp_classification_schema():
    data = {
        "primary_category": "hardware",
        "secondary_categories": ["it_services"],
        "sub_category": "networking_equipment",
        "procurement_type": "product",
        "confidence": 0.94,
        "keywords": ["router", "switch", "firewall"],
        "short_reason": "The RFP primarily requests physical networking equipment.",
    }
    result = RFPClassificationResult.model_validate(data)
    assert result.primary_category == "hardware"
    assert result.secondary_categories == ["it_services"]
    assert result.procurement_type == "product"
    assert result.confidence == 0.94


def test_invalid_category_rejected():
    data = {
        "primary_category": "quantum_computing_devices",  # Invalid category
        "secondary_categories": [],
        "sub_category": "quantum",
        "procurement_type": "product",
        "confidence": 0.8,
        "keywords": ["quantum"],
        "short_reason": "Invalid category test",
    }
    with pytest.raises(ValidationError) as exc:
        RFPClassificationResult.model_validate(data)
    assert "allowed taxonomy" in str(exc.value)


def test_invalid_secondary_category_rejected():
    data = {
        "primary_category": "software",
        "secondary_categories": ["artificial_super_intelligence"],  # Invalid
        "sub_category": "ai",
        "procurement_type": "product",
        "confidence": 0.8,
        "keywords": [],
        "short_reason": "Invalid secondary test",
    }
    with pytest.raises(ValidationError) as exc:
        RFPClassificationResult.model_validate(data)
    assert "allowed taxonomy" in str(exc.value)


def test_invalid_procurement_type_rejected():
    data = {
        "primary_category": "software",
        "secondary_categories": [],
        "sub_category": "app",
        "procurement_type": "donation_grant",  # Invalid type
        "confidence": 0.8,
        "keywords": [],
        "short_reason": "Invalid type test",
    }
    with pytest.raises(ValidationError) as exc:
        RFPClassificationResult.model_validate(data)
    assert "allowed types" in str(exc.value)


def test_invalid_confidence_rejected():
    # Confidence > 1.0
    with pytest.raises(ValidationError):
        RFPClassificationResult.model_validate({
            "primary_category": "software",
            "sub_category": "saas",
            "procurement_type": "subscription",
            "confidence": 1.45,
            "short_reason": "Out of range",
        })

    # Confidence < 0.0
    with pytest.raises(ValidationError):
        RFPClassificationResult.model_validate({
            "primary_category": "software",
            "sub_category": "saas",
            "procurement_type": "subscription",
            "confidence": -0.2,
            "short_reason": "Out of range",
        })


def test_multiple_categories_handled_correctly():
    data = {
        "primary_category": "hardware",
        "secondary_categories": ["it_services", "telecommunications"],
        "sub_category": "routers",
        "procurement_type": "mixed",
        "confidence": 0.88,
        "keywords": ["telecom", "hardware", "router"],
        "short_reason": "Hardware purchase with setup services.",
    }
    result = RFPClassificationResult.model_validate(data)
    assert len(result.secondary_categories) == 2
    assert "it_services" in result.secondary_categories
    assert "telecommunications" in result.secondary_categories


# =====================================================================
# 2. Section 17 Specification Example Cases
# =====================================================================

@pytest.mark.parametrize(
    "case_title,expected_primary,expected_sub,expected_type",
    [
        ("Supply of 500 Dell Desktop Computers", "hardware", "computers", "product"),
        ("Development and Maintenance of Government E-Learning Platform", "it_services", "e_learning_platform", "service"),
        ("Microsoft 365 Enterprise Subscription", "software", "saas", "subscription"),
        ("Cloud Infrastructure Migration to AWS", "cloud", "cloud_migration", "implementation"),
        ("Supply and Installation of Network Switches and Routers", "hardware", "networking_equipment", "product"),
        ("Penetration Testing and Security Assessment", "cybersecurity", "security_assessment", "service"),
    ],
)
def test_spec_example_cases_validation(case_title, expected_primary, expected_sub, expected_type):
    result = RFPClassificationResult.model_validate({
        "primary_category": expected_primary,
        "sub_category": expected_sub,
        "procurement_type": expected_type,
        "confidence": 0.95,
        "keywords": ["test", expected_primary],
        "short_reason": f"Objective relates to {expected_primary}",
    })
    assert result.primary_category == expected_primary
    assert result.primary_category in ALLOWED_PRIMARY_CATEGORIES
    assert result.procurement_type == expected_type
    assert result.procurement_type in ALLOWED_PROCUREMENT_TYPES


# =====================================================================
# 3. Service Unit Tests with Mocked AI Calls
# =====================================================================

def test_classify_rfp_empty_title_does_not_call_ai():
    service = RFPClassificationService()
    with patch.object(service, "_resolve_provider_and_client") as mock_resolve:
        res = service.classify_rfp({"title": ""})
        assert res is None
        mock_resolve.assert_not_called()


def test_classify_rfp_successful_mocked_openai():
    service = RFPClassificationService(max_retries=1)
    mock_ai_response = json.dumps({
        "primary_category": "hardware",
        "secondary_categories": ["it_services"],
        "sub_category": "computers",
        "procurement_type": "product",
        "confidence": 0.96,
        "keywords": ["laptops", "desktops"],
        "short_reason": "Procurement for 500 enterprise laptops.",
    })

    with patch.object(service, "_resolve_provider_and_client") as mock_resolve:
        mock_client = MagicMock()
        mock_resolve.return_value = ("openai", mock_client, "gpt-4o", 0.0)

        with patch.object(service, "_call_ai_model", return_value=mock_ai_response):
            result = service.classify_rfp({"title": "Supply of 500 Enterprise Laptops"})

            assert result is not None
            assert result.primary_category == "hardware"
            assert result.sub_category == "computers"
            assert result.procurement_type == "product"
            assert result.confidence == 0.96


def test_classify_rfp_rate_limit_retry_succeeds():
    service = RFPClassificationService(max_retries=2)
    mock_ai_response = json.dumps({
        "primary_category": "software",
        "secondary_categories": [],
        "sub_category": "subscription",
        "procurement_type": "subscription",
        "confidence": 0.91,
        "keywords": ["saas", "license"],
        "short_reason": "Subscription software.",
    })

    with patch.object(service, "_resolve_provider_and_client") as mock_resolve:
        mock_client = MagicMock()
        mock_resolve.return_value = ("openai", mock_client, "gpt-4o", 0.0)

        # First call raises rate limit 429, second call succeeds
        with patch.object(
            service,
            "_call_ai_model",
            side_effect=[Exception("Error 429: rate limit reached"), mock_ai_response],
        ):
            with patch("time.sleep", return_value=None):
                result = service.classify_rfp({"title": "Annual SaaS License"})

                assert result is not None
                assert result.primary_category == "software"
                assert result.procurement_type == "subscription"


def test_classify_rfp_timeout_returns_none_without_crash():
    service = RFPClassificationService(max_retries=1)

    with patch.object(service, "_resolve_provider_and_client") as mock_resolve:
        mock_client = MagicMock()
        mock_resolve.return_value = ("openai", mock_client, "gpt-4o", 0.0)

        with patch.object(
            service,
            "_call_ai_model",
            side_effect=TimeoutError("Request timed out"),
        ):
            with patch("time.sleep", return_value=None):
                result = service.classify_rfp({"title": "Network Hardware Deployment"})
                # Must return None and not crash
                assert result is None


def test_classify_existing_rfp_idempotency():
    service = RFPClassificationService()
    mock_db = MagicMock()

    mock_rfp = MagicMock()
    mock_rfp.id = 101
    mock_rfp.classification_status = "completed"
    mock_rfp.primary_category = "cybersecurity"

    mock_db.query.return_value.filter.return_value.first.return_value = mock_rfp

    with patch.object(service, "classify_rfp") as mock_classify:
        # force=False should skip re-classification
        res = service.classify_existing_rfp(mock_db, rfp_id=101, force=False)
        assert res.id == 101
        mock_classify.assert_not_called()

        # force=True should re-classify
        mock_classify.return_value = RFPClassificationResult(
            primary_category="cybersecurity",
            sub_category="soc",
            procurement_type="service",
            confidence=0.99,
            keywords=["soc"],
            short_reason="Updated",
        )
        res_forced = service.classify_existing_rfp(mock_db, rfp_id=101, force=True)
        assert res_forced.id == 101
        assert mock_classify.call_count == 1


# =====================================================================
# 4. Ingestion Pipeline Integration & Duplicate Exclusion Tests
# =====================================================================

def test_pipeline_duplicate_rfp_does_not_call_ai_classifier():
    """
    CRITICAL REQUIREMENT:
    If an RFP is already a duplicate:
    DO NOT call the AI classification API.
    """
    rfp_service = RFPService()
    mock_db = MagicMock()

    item_duplicate = {
        "title": "Supply of Dell Desktop Computers",
        "description": "Standard procurement for 500 desktop systems with delivery details.",
        "reference_number": "REF-DELL-500",
        "submission_deadline": "2026-10-15",
    }

    # Mock duplicate detection to return an existing RFP record
    mock_existing_rfp = MagicMock()
    mock_existing_rfp.id = 55

    with patch("app.services.rfp_service.find_duplicate", return_value=mock_existing_rfp):
        with patch("app.services.rfp_service.compare_and_update", return_value=(mock_existing_rfp, False)):
            with patch("app.services.rfp_service.rfp_classification_service.classify_rfp") as mock_classify:
                with patch("app.services.rfp_service.SentenceTransformer") as mock_st:
                    mock_st.return_value.encode.return_value.tolist.return_value = [0.1] * 384

                    results = rfp_service.process_extracted_data_synchronous(
                        db=mock_db,
                        extracted_data=[item_duplicate],
                        url_str="http://example.com/procurements",
                        notify=False,
                    )

                    assert len(results) == 1
                    assert results[0]["status"] == "ignored"
                    # Verification: AI classification MUST NOT be called for duplicates
                    mock_classify.assert_not_called()


def test_pipeline_new_rfp_calls_ai_and_saves_classification():
    """
    Verifies that a genuinely new candidate triggers AI classification,
    validates the output, and attaches the fields to the persisted RFP.
    """
    rfp_service = RFPService()
    mock_db = MagicMock()

    item_new = {
        "title": "Cloud Infrastructure Migration to AWS",
        "description": "Enterprise wide cloud migration covering database and application workloads.",
        "reference_number": "AWS-MIG-2026",
        "submission_deadline": "2026-11-20",
    }

    mock_classification = RFPClassificationResult(
        primary_category="cloud",
        secondary_categories=["it_services"],
        sub_category="cloud_migration",
        procurement_type="implementation",
        confidence=0.95,
        keywords=["aws", "cloud", "migration"],
        short_reason="Primary objective is migrating on-premise infrastructure to AWS cloud.",
    )

    with patch("app.services.rfp_service.find_duplicate", return_value=None):
        with patch("app.services.rfp_service.rfp_repo.get_similar_by_embedding", return_value=None):
            with patch(
                "app.services.rfp_service.rfp_classification_service.classify_rfp",
                return_value=mock_classification,
            ) as mock_classify:
                with patch("app.services.rfp_service.SentenceTransformer") as mock_st:
                    mock_st.return_value.encode.return_value.tolist.return_value = [0.1] * 384

                    results = rfp_service.process_extracted_data_synchronous(
                        db=mock_db,
                        extracted_data=[item_new],
                        url_str="http://example.com/cloud-tender",
                        notify=False,
                    )

                    assert len(results) == 1
                    assert results[0]["status"] == "inserted"
                    mock_classify.assert_called_once()

                    # Verify DB add was called with model carrying the classification
                    assert mock_db.add.called
                    saved_rfp = mock_db.add.call_args[0][0]
                    assert saved_rfp.primary_category == "cloud"
                    assert saved_rfp.sub_category == "cloud_migration"
                    assert saved_rfp.procurement_type == "implementation"
                    assert saved_rfp.confidence == 0.95
                    assert saved_rfp.classification_status == "completed"


def test_pipeline_ai_failure_preserves_rfp_and_does_not_crash_job():
    """
    CRITICAL REQUIREMENT:
    If AI classification fails for one RFP, the RFP must still be preserved
    with classification_status='failed', and subsequent RFPs must continue processing.
    """
    rfp_service = RFPService()
    mock_db = MagicMock()

    item_failing = {
        "title": "Hospital Surgical Equipment Supply",
        "description": "Procurement of specialized laparoscopic surgery suites.",
        "reference_number": "MED-001",
        "submission_deadline": "2026-12-01",
    }
    item_succeeding = {
        "title": "Office Stationery and Paper Supplies",
        "description": "Annual supply contract for A4 paper and office stationery.",
        "reference_number": "OFF-002",
        "submission_deadline": "2026-12-05",
    }

    mock_success_classification = RFPClassificationResult(
        primary_category="office_supplies",
        secondary_categories=[],
        sub_category="stationery",
        procurement_type="product",
        confidence=0.98,
        keywords=["paper", "stationery"],
        short_reason="Annual office consumables.",
    )

    with patch("app.services.rfp_service.find_duplicate", return_value=None):
        with patch("app.services.rfp_service.rfp_repo.get_similar_by_embedding", return_value=None):
            # First item fails classification (returns None), second item succeeds
            with patch(
                "app.services.rfp_service.rfp_classification_service.classify_rfp",
                side_effect=[None, mock_success_classification],
            ):
                with patch("app.services.rfp_service.SentenceTransformer") as mock_st:
                    mock_st.return_value.encode.return_value.tolist.return_value = [0.1] * 384

                    results = rfp_service.process_extracted_data_synchronous(
                        db=mock_db,
                        extracted_data=[item_failing, item_succeeding],
                        url_str="http://example.com/listings",
                        notify=False,
                    )

                    assert len(results) == 2
                    assert results[0]["status"] == "inserted"
                    assert results[1]["status"] == "inserted"

                    # Check that both RFPs were added to db
                    assert mock_db.add.call_count == 2
                    first_saved = mock_db.add.call_args_list[0][0][0]
                    second_saved = mock_db.add.call_args_list[1][0][0]

                    # First RFP preserved with failed classification status
                    assert first_saved.title == "Hospital Surgical Equipment Supply"
                    assert first_saved.classification_status == "failed"

                    # Second RFP saved with completed status
                    assert second_saved.title == "Office Stationery and Paper Supplies"
                    assert second_saved.classification_status == "completed"
                    assert second_saved.primary_category == "office_supplies"


def test_reusing_agent_extracted_classification_skips_standalone_call():
    """
    Verify cost-optimization: when extraction agent already provides category classification,
    the pipeline reuses it directly without invoking the standalone classification LLM.
    """
    mock_db = MagicMock()
    rfp_service = RFPService()

    pre_classified_item = {
        "title": "Supply and Installation of Cloud Virtualization Platform",
        "description": "Procurement of enterprise virtualization licenses and hypervisor migration.",
        "reference_number": "VIRT-2026-99",
        "submission_deadline": "2026-11-20",
        "primary_category": "software",
        "sub_category": "virtualization",
        "procurement_type": "software_license",
        "confidence": 0.96,
        "keywords": ["virtualization", "licenses", "hypervisor"],
        "short_reason": "Enterprise software license procurement.",
    }

    with patch("app.services.rfp_service.find_duplicate", return_value=None):
        with patch("app.services.rfp_service.rfp_repo.get_similar_by_embedding", return_value=None):
            with patch(
                "app.services.rfp_service.rfp_classification_service.classify_rfp"
            ) as mock_classify_rfp:
                with patch("app.services.rfp_service.SentenceTransformer") as mock_st:
                    mock_st.return_value.encode.return_value.tolist.return_value = [0.1] * 384

                    results = rfp_service.process_extracted_data_synchronous(
                        db=mock_db,
                        extracted_data=[pre_classified_item],
                        url_str="http://example.com/virtualization-rfp",
                        notify=False,
                    )

                    assert len(results) == 1
                    assert results[0]["status"] == "inserted"

                    # Crucial check: classify_rfp must NOT be called (0 extra API calls)
                    mock_classify_rfp.assert_not_called()

                    # Check that saved RFP has pre-classified values
                    assert mock_db.add.call_count == 1
                    saved_rfp = mock_db.add.call_args_list[0][0][0]

                    assert saved_rfp.title == "Supply and Installation of Cloud Virtualization Platform"
                    assert saved_rfp.primary_category == "software"
                    assert saved_rfp.sub_category == "virtualization"
                    assert saved_rfp.procurement_type == "software_license"
                    assert saved_rfp.confidence == 0.96
                    assert saved_rfp.classification_status == "completed"
                    assert saved_rfp.classification_reason == "Enterprise software license procurement."

