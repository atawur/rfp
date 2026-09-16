from typing import Optional
from sqlalchemy.orm import Session
from app.models.rfp import RFP
from app.repositories.rfp_repo import rfp_repo

def find_duplicate(db: Session, rfp_data: dict) -> Optional[RFP]:
    """
    Implements prioritized identity signals according to spec Section 8:
    1. external_rfp_id
    2. reference_number
    3. source_url + title (prevents collapsing multiple RFPs on listing pages)
    4. normalized title + deadline
    """
    # 1. External RFP ID
    ext_id = rfp_data.get("external_rfp_id")
    if ext_id and str(ext_id).strip():
        existing = rfp_repo.get_by_external_id(db, external_id=str(ext_id).strip())
        if existing:
            return existing

    # 2. Reference Number
    ref_no = rfp_data.get("reference_number")
    if ref_no and str(ref_no).strip():
        existing = rfp_repo.get_by_reference_number(db, reference_number=str(ref_no).strip())
        if existing:
            return existing

    # 3. Source URL + Title match (listing pages contain multiple RFPs at the same source_url)
    source_url = rfp_data.get("source_url")
    title = rfp_data.get("title")
    if source_url and str(source_url).strip() and title and str(title).strip():
        existing = rfp_repo.get_by_source_url_and_title(
            db, source_url=str(source_url).strip(), title=str(title).strip()
        )
        if existing:
            return existing

    # 4. Title + Deadline match
    deadline = rfp_data.get("submission_deadline")
    if title and str(title).strip() and deadline:
        existing = rfp_repo.get_by_title_and_deadline(
            db, title=str(title).strip(), deadline=deadline
        )
        if existing:
            return existing

    return None
