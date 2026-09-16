from sqlalchemy.orm import Session
from app.models.rfp import RFP
from app.models.rfp_version import RFPVersion
from app.models.rfp_change import RFPChange
import json

def compare_and_update(db: Session, existing_rfp: RFP, new_data: dict) -> tuple[RFP, bool]:
    """
    Compares existing RFP with new data. If changes are meaningful,
    creates a new version snapshot and change logs.
    """
    fields_to_check = ['title', 'submission_deadline', 'estimated_budget', 'status']
    changes_detected = []
    
    for field in fields_to_check:
        old_val = getattr(existing_rfp, field, None)
        new_val = new_data.get(field)

        if new_val is not None:
            old_str = str(old_val).strip() if old_val is not None else ""
            new_str = str(new_val).strip()
            if old_str != new_str:
                changes_detected.append({
                    "field": field,
                    "old_value": old_str,
                    "new_value": new_str
                })
            
    if changes_detected:
        # 1. Create a version snapshot
        # Simple dict conversion for snapshot
        snapshot = {c.name: getattr(existing_rfp, c.name) for c in existing_rfp.__table__.columns}
        # handle datetime serialization
        snapshot = {k: str(v) for k, v in snapshot.items()}

        version_no = len(existing_rfp.versions) + 1
        new_version = RFPVersion(
            rfp_id=existing_rfp.id,
            version_no=version_no,
            snapshot=snapshot
        )
        db.add(new_version)

        # 2. Record changes
        for change in changes_detected:
            log_entry = RFPChange(
                rfp_id=existing_rfp.id,
                versions=f"{version_no}->{version_no+1}",
                field=change["field"],
                old_value=json.dumps(change["old_value"]),
                new_value=json.dumps(change["new_value"])
            )
            db.add(log_entry)

            # Apply update to the existing rfp object
            setattr(existing_rfp, change["field"], change["new_value"])

        db.commit()
        db.refresh(existing_rfp)
        return existing_rfp, True

    return existing_rfp, False
