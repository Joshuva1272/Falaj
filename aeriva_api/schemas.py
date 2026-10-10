from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class ScenarioRequest(BaseModel):
    market: str
    month: str
    lever: str
    values: Dict[str, Any]
    published_occupancy: Optional[float] = None
    
class RefitRequest(BaseModel):
    # Depending on how files are passed, it might be multipart/form-data. For now, empty triggers refit.
    pass

class MetaResponse(BaseModel):
    months: List[str]
    markets: Dict[str, Any]
    data_version: str

class CardRequest(BaseModel):
    scenario: Dict[str, Any] # Or specific fields
