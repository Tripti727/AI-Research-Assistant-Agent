from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from backend.models import ReqBody, ResearchResult
from backend.agent_logic import run_research_agent
from backend.database import SessionLocal, init_db, ResearchHistoryModel

app = FastAPI()

@app.on_event("startup")
def startup_event():
    init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"msg": "Server is running with Database integration!"}

@app.post("/research", response_model=ResearchResult)
def get_research(req: ReqBody, db: Session = Depends(get_db)):
    try:
        h_list = [{"query": x.query, "summary": x.summary} for x in req.history]
        result = run_research_agent(query=req.query, history=h_list)
        
        summary_text = " ".join(result.executive_summary_points)
        sources_json = json.dumps([s.dict() for s in result.sources])
        
        db_item = ResearchHistoryModel(
            query=req.query,
            topic=result.topic,
            summary=summary_text,
            sources=sources_json
        )
        db.add(db_item)
        db.commit()
        
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))