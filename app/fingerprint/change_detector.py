import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models.content_fingerprint import ContentFingerprint
from app.models.rfp import RFP
from app.fingerprint.hasher import content_fingerprinter
from app.discovery.candidate_discovery import RFPCandidate

logger = logging.getLogger(__name__)

@dataclass
class ChangeEvaluation:
    status: str  # "NEW" | "UNCHANGED" | "CHANGED"
    normalized_url: str
    content_hash: str
    existing_fingerprint: Optional[ContentFingerprint] = None
    existing_rfp_id: Optional[int] = None

    @property
    def should_skip(self) -> bool:
        return self.status == "UNCHANGED"


class ChangeDetectionService:
    """
    Evaluates candidates against historical fingerprints in the database:
    - NEW: first time candidate is discovered.
    - UNCHANGED: same candidate & identical SHA-256 hash. SKIPS further processing.
    - CHANGED: content, deadline, or title changed. Triggers re-extraction.
    """

    def evaluate_candidate(
        self,
        db: Session,
        candidate: RFPCandidate,
        website_id: Optional[int] = None
    ) -> ChangeEvaluation:
        norm_url = content_fingerprinter.normalize_url(candidate.candidate_id or candidate.source_url)
        c_hash = content_fingerprinter.compute_hash(candidate.normalized_content)

        # 1. Lookup existing fingerprint by normalized_url
        existing_fp = (
            db.query(ContentFingerprint)
            .filter(
                (ContentFingerprint.normalized_url == norm_url) |
                (ContentFingerprint.source_url == candidate.source_url)
            )
            .order_by(ContentFingerprint.id.desc())
            .first()
        )

        now = datetime.now(timezone.utc)

        if existing_fp:
            if existing_fp.content_hash == c_hash:
                # UNCHANGED: update last_seen_at and skip
                existing_fp.last_seen_at = now  # type: ignore
                db.commit()
                logger.info(f"[ChangeDetection] UNCHANGED for {norm_url} (hash={c_hash[:8]}). Skipping LLM.")
                return ChangeEvaluation(
                    status="UNCHANGED",
                    normalized_url=norm_url,
                    content_hash=c_hash,
                    existing_fingerprint=existing_fp,
                    existing_rfp_id=existing_fp.rfp_id,
                )
            else:
                # CHANGED: content hash has updated
                logger.info(
                    f"[ChangeDetection] CHANGED for {norm_url}: "
                    f"old_hash={existing_fp.content_hash[:8]} -> new_hash={c_hash[:8]}"
                )
                existing_fp.last_seen_at = now  # type: ignore
                db.commit()
                return ChangeEvaluation(
                    status="CHANGED",
                    normalized_url=norm_url,
                    content_hash=c_hash,
                    existing_fingerprint=existing_fp,
                    existing_rfp_id=existing_fp.rfp_id,
                )

        # 2. Check if an RFP for the same URL already exists in the RFP table
        existing_rfp = db.query(RFP).filter(
            (RFP.source_url == candidate.source_url) |
            (RFP.normalized_url == norm_url)
        ).first()
        if existing_rfp:
            if existing_rfp.content_hash == c_hash:
                logger.info(f"[ChangeDetection] UNCHANGED (matched RFP {existing_rfp.id} content_hash {c_hash[:8]}). Skipping LLM.")
                fp = ContentFingerprint(
                    source_url=candidate.source_url,
                    normalized_url=norm_url,
                    content_hash=c_hash,
                    website_id=website_id,
                    rfp_id=existing_rfp.id,
                    first_seen_at=existing_rfp.first_seen_at or now,
                    last_seen_at=now,
                    last_processed_at=now,
                )
                db.add(fp)
                db.commit()
                return ChangeEvaluation(
                    status="UNCHANGED",
                    normalized_url=norm_url,
                    content_hash=c_hash,
                    existing_fingerprint=fp,
                    existing_rfp_id=existing_rfp.id,
                )
            else:
                logger.info(f"[ChangeDetection] CHANGED (matched RFP {existing_rfp.id} with new hash {c_hash[:8]}).")
                return ChangeEvaluation(
                    status="CHANGED",
                    normalized_url=norm_url,
                    content_hash=c_hash,
                    existing_fingerprint=None,
                    existing_rfp_id=existing_rfp.id,
                )


        logger.info(f"[ChangeDetection] NEW candidate discovered for {norm_url} (hash={c_hash[:8]}).")
        return ChangeEvaluation(
            status="NEW",
            normalized_url=norm_url,
            content_hash=c_hash,
            existing_fingerprint=None,
            existing_rfp_id=None,
        )

    def record_or_update_fingerprint(
        self,
        db: Session,
        candidate: RFPCandidate,
        rfp_id: Optional[int] = None,
        website_id: Optional[int] = None,
        extraction_version: int = 1,
        parser_version: int = 1,
    ) -> ContentFingerprint:
        norm_url = content_fingerprinter.normalize_url(candidate.candidate_id or candidate.source_url)
        c_hash = content_fingerprinter.compute_hash(candidate.normalized_content)
        now = datetime.now(timezone.utc)

        existing_fp = (
            db.query(ContentFingerprint)
            .filter(ContentFingerprint.normalized_url == norm_url)
            .order_by(ContentFingerprint.id.desc())
            .first()
        )

        if existing_fp:
            existing_fp.content_hash = c_hash  # type: ignore
            existing_fp.last_seen_at = now  # type: ignore
            existing_fp.last_processed_at = now  # type: ignore
            existing_fp.extraction_version = extraction_version  # type: ignore
            existing_fp.parser_version = parser_version  # type: ignore
            if rfp_id:
                existing_fp.rfp_id = rfp_id  # type: ignore
            db.commit()
            return existing_fp
        else:
            fp = ContentFingerprint(
                source_url=candidate.source_url,
                normalized_url=norm_url,
                content_hash=c_hash,
                website_id=website_id,
                rfp_id=rfp_id,
                extraction_version=extraction_version,
                parser_version=parser_version,
                first_seen_at=now,
                last_seen_at=now,
                last_processed_at=now,
            )
            db.add(fp)
            db.commit()
            return fp

change_detection_service = ChangeDetectionService()
