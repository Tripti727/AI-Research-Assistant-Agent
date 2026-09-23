import os
import json
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient
from backend.models import ResearchResult, ResearchSource

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

def run_research_agent(query: str, history: list = None) -> ResearchResult:
    web_data = ""
    sources = []
    
    today = datetime.now().strftime("%Y-%m-%d")
    search_q = f"{query} (Date: {today})"
    
    try:
        resp = tavily.search(query=search_q, max_results=2, include_raw_content=False)
        for r in resp.get("results", []):
            t = r.get('title', 'Title')
            u = r.get('url', '#')
            c = r.get('content', '')
            web_data += f"Title: {t}\nURL: {u}\nContent: {c}\n\n"
            sources.append(ResearchSource(title=t, url=u))
    except Exception as e:
        web_data = f"Search failed: {e}"
    
    ctx = ""
    if history:
        for h in history[-3:]:
            ctx += f"Q: {h['query']}\nAns: {h['summary']}\n"

    sys_prompt = (
        "You are a helpful research assistant. "
        "Read the web data and answer the query. "
        "Give executive summary in bullet points (executive_summary_points), not in long paragraphs."
    )
    
    usr_prompt = f"History:\n{ctx}\n\nQuery:\n{query}\n\nData:\n{web_data}"
    schema = ResearchResult.model_json_schema()

    response = groq.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {"role": "system", "content": sys_prompt + f"\nOutput JSON matching:\n{json.dumps(schema)}"},
            {"role": "user", "content": usr_prompt}
        ],
        temperature=0.3,
        max_tokens=800,
        response_format={"type": "json_object"}
    )

    data = json.loads(response.choices[0].message.content)
    data["sources"] = [s.dict() for s in sources]
    
    return ResearchResult(**data)