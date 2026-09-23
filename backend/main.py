from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from backend.agent_logic import run_research_agent
from backend.models import ResearchResult

app = FastAPI()

class ChatItem(BaseModel):
    query: str
    summary: str

class ReqBody(BaseModel):
    query: str
    history: Optional[List[ChatItem]] = []

@app.get("/")
def home():
    return {"msg": "Server is running"}

@app.post("/research", response_model=ResearchResult)
def get_research(req: ReqBody):
    try:
        h_list = [{"query": x.query, "summary": x.summary} for x in req.history]
        return run_research_agent(query=req.query, history=h_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))