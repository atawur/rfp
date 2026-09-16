from typing import Dict, Any
from app.agents.rfp_agent.schemas import RFPExtractionSchema
import logging

logger = logging.getLogger(__name__)

class ExtractionPipeline:
    def map_to_db_schema(self, extracted_data: RFPExtractionSchema, source_url: str) -> Dict[str, Any]:
        """
        Maps the strictly typed Pydantic output from the LLM to the dictionary 
        expected by the RFPService for database persistence.
        """
        logger.info(f"Mapping extracted data for {source_url} to DB schema.")
        
        mapped_data = extracted_data.model_dump()
        mapped_data["source_url"] = source_url
        mapped_data["status"] = "NEW" # Default status for a newly discovered RFP
        
        # In a real pipeline, we might also execute business rules here
        # e.g., if validation_flags has entries, set status to NEEDS_REVIEW
        if mapped_data.get("validation_flags"):
            mapped_data["status"] = "NEEDS_REVIEW"
            
        return mapped_data

extraction_pipeline = ExtractionPipeline()
