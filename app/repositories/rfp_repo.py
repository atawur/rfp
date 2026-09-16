from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from app.repositories.base import BaseRepository
from app.models.rfp import RFP
from app.schemas.rfp import RFPCreate, RFPUpdate

class RFPRepository(BaseRepository[RFP, RFPCreate, RFPUpdate]):
    def get_by_source_url(self, db: Session, *, source_url: str) -> Optional[RFP]:
        return db.query(RFP).filter(RFP.source_url == source_url).first()

    def get_by_source_url_and_title(self, db: Session, *, source_url: str, title: str) -> Optional[RFP]:
        return db.query(RFP).filter(
            RFP.source_url == source_url,
            func.lower(func.trim(RFP.title)) == func.lower(func.trim(title))
        ).first()

    def get_by_external_id(self, db: Session, *, external_id: str) -> Optional[RFP]:
        return db.query(RFP).filter(RFP.external_rfp_id == external_id).first()

    def get_by_reference_number(self, db: Session, *, reference_number: str) -> Optional[RFP]:
        return db.query(RFP).filter(RFP.reference_number == reference_number).first()

    def get_by_title_and_deadline(self, db: Session, *, title: str, deadline: any) -> Optional[RFP]:
        return db.query(RFP).filter(
            func.lower(func.trim(RFP.title)) == func.lower(func.trim(title)),
            RFP.submission_deadline == deadline
        ).first()

    def get_similar_by_embedding(self, db: Session, embedding: List[float], threshold: float = 0.15) -> Optional[RFP]:
        return db.query(RFP).filter(
            RFP.embedding.cosine_distance(embedding) < threshold
        ).first()

    def _build_filter_query(
        self,
        db: Session,
        *,
        website_id: Optional[int] = None,
        category: Optional[str] = None,
        sub_category: Optional[str] = None,
        procurement_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ):
        query = db.query(RFP)

        # Website filter
        if website_id is not None and website_id > 0:
            query = query.filter(RFP.website_id == website_id)

        # Category filter
        if category and category.strip():
            cat = category.strip().lower()
            if cat == "unclassified":
                query = query.filter(
                    or_(
                        RFP.primary_category.is_(None),
                        func.lower(RFP.primary_category) == "unclassified",
                        RFP.primary_category == "",
                    )
                )
            else:
                clean_cat = cat.replace(" ", "_").replace("-", "_")
                query = query.filter(
                    or_(
                        func.lower(RFP.primary_category) == cat,
                        func.lower(RFP.primary_category) == clean_cat,
                    )
                )

        # Sub-category filter
        if sub_category and sub_category.strip():
            sub = sub_category.strip().lower()
            query = query.filter(func.lower(RFP.sub_category) == sub)

        # Procurement type filter
        if procurement_type and procurement_type.strip():
            ptype = procurement_type.strip().lower()
            query = query.filter(func.lower(RFP.procurement_type) == ptype)

        # Status filter
        if status and status.strip() and status.strip().upper() != "ALL":
            query = query.filter(func.upper(RFP.status) == status.strip().upper())

        # Search term across text and category fields
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(RFP.title).like(term),
                    func.lower(RFP.organization).like(term),
                    func.lower(RFP.reference_number).like(term),
                    func.lower(RFP.primary_category).like(term),
                    func.lower(RFP.sub_category).like(term),
                    func.lower(RFP.procurement_type).like(term),
                )
            )

        return query

    def get_filtered_rfps(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        website_id: Optional[int] = None,
        category: Optional[str] = None,
        sub_category: Optional[str] = None,
        procurement_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[RFP]:
        items, _ = self.get_filtered_rfps_with_total(
            db,
            skip=skip,
            limit=limit,
            website_id=website_id,
            category=category,
            sub_category=sub_category,
            procurement_type=procurement_type,
            status=status,
            search=search,
        )
        return items

    def get_filtered_rfps_with_total(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        website_id: Optional[int] = None,
        category: Optional[str] = None,
        sub_category: Optional[str] = None,
        procurement_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[RFP], int]:
        base_query = self._build_filter_query(
            db,
            website_id=website_id,
            category=category,
            sub_category=sub_category,
            procurement_type=procurement_type,
            status=status,
            search=search,
        )
        total = base_query.count()
        items = (
            base_query.options(joinedload(RFP.website))
            .order_by(RFP.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

rfp_repo = RFPRepository(RFP)
