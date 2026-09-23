from pydantic import BaseModel
from typing import List

class ResearchSource(BaseModel):
    title: str
    url: str

class ResearchResult(BaseModel):
    is_relevant: bool
    topic: str
    executive_summary_points: List[str]
    key_findings: List[str] = []
    sources: List[ResearchSource] = []