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

def run_research_agent(query: str, history: list = None):
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
        "You are a specialized AI Research Assistant. Your job is ONLY to answer academic, technical, or research-related queries. "
        "Check the user query. If the query is off-topic (unrelated to research, science, technology, or studies, like movies, cooking, personal chat, etc.), "
        "set 'is_relevant' to false, and in 'executive_summary_points' write a polite refusal message like: "
        "'I am a specialized research assistant. I can only provide information on research and technical topics. Please ask a study or research-related question.' "
        "If the query is relevant, set 'is_relevant' to true and provide the summary based on the web data in bullet points."
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