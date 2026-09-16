from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, declared_attr

from app.db.base_class import Base

class RFPDocument(Base):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "rfp_document"
    
    id = Column(Integer, primary_key=True, index=True)
    rfp_id = Column(Integer, ForeignKey("rfp.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=True)
    source_url = Column(String, nullable=False)
    storage_url = Column(String, nullable=True)
    hash = Column(String, nullable=True)

    rfp = relationship("RFP", back_populates="documents")
