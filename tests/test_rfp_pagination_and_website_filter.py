import pytest
import uuid
import app.db.base  # Register all SQLAlchemy models
from app.db.session import SessionLocal
from app.models.rfp import RFP
from app.models.website import Website
from app.services.rfp_service import rfp_service


def test_rfp_pagination_and_website_filter():
    db = SessionLocal()
    slug = uuid.uuid4().hex[:8]
    website_a = Website(
        name=f"Site A {slug}",
        base_url=f"https://site-a-{slug}.example.com",
        start_url=f"https://site-a-{slug}.example.com/tenders",
    )
    website_b = Website(
        name=f"Site B {slug}",
        base_url=f"https://site-b-{slug}.example.com",
        start_url=f"https://site-b-{slug}.example.com/tenders",
    )
    db.add_all([website_a, website_b])
    db.commit()
    db.refresh(website_a)
    db.refresh(website_b)

    rfp_ids = []
    try:
        # Create 3 RFPs for website A and 2 for website B
        for i in range(3):
            rfp = RFP(
                title=f"RFP A{i} {slug}",
                source_url=f"https://site-a-{slug}.example.com/rfp/{i}",
                website_id=website_a.id,
                status="OPEN",
                primary_category="software",
            )
            db.add(rfp)
            db.flush()
            rfp_ids.append(rfp.id)

        for i in range(2):
            rfp = RFP(
                title=f"RFP B{i} {slug}",
                source_url=f"https://site-b-{slug}.example.com/rfp/{i}",
                website_id=website_b.id,
                status="NEW",
                primary_category="hardware",
            )
            db.add(rfp)
            db.flush()
            rfp_ids.append(rfp.id)

        db.commit()

        # 1. Test filtering by website_a
        res_a = rfp_service.get_paginated_rfps(
            db, page=1, size=10, website_id=website_a.id, search=slug
        )
        assert res_a["total"] == 3
        assert len(res_a["items"]) == 3
        assert res_a["pages"] == 1
        assert all(item.website_id == website_a.id for item in res_a["items"])
        assert all(item.website_name == f"Site A {slug}" for item in res_a["items"])

        # 2. Test filtering by website_b
        res_b = rfp_service.get_paginated_rfps(
            db, page=1, size=10, website_id=website_b.id, search=slug
        )
        assert res_b["total"] == 2
        assert len(res_b["items"]) == 2
        assert all(item.website_id == website_b.id for item in res_b["items"])
        assert all(item.website_name == f"Site B {slug}" for item in res_b["items"])

        # 3. Test pagination: page 1 of size 2 across all RFPs with this slug
        res_all_p1 = rfp_service.get_paginated_rfps(
            db, page=1, size=2, search=slug
        )
        assert res_all_p1["total"] == 5
        assert res_all_p1["pages"] == 3
        assert len(res_all_p1["items"]) == 2
        assert res_all_p1["page"] == 1
        assert res_all_p1["size"] == 2

        # 4. Test page 3 (last page of 5 items with size 2 -> 1 item)
        res_all_p3 = rfp_service.get_paginated_rfps(
            db, page=3, size=2, search=slug
        )
        assert len(res_all_p3["items"]) == 1
        assert res_all_p3["page"] == 3

    finally:
        # Cleanup
        if rfp_ids:
            db.query(RFP).filter(RFP.id.in_(rfp_ids)).delete(synchronize_session=False)
        db.delete(website_a)
        db.delete(website_b)
        db.commit()
        db.close()
