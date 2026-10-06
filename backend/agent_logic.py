import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from backend.models import ResearchResult, ResearchSource
from dotenv import load_dotenv

load_dotenv()

def run_research_agent(query: str, history: list = None) -> ResearchResult:
    # Initialize Groq LLM
    llm = ChatGroq(
        model="qwen/qwen3.8-27b",
        temperature=0.1,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )

    # Bind structured output schema to LLM
    structured_llm = llm.with_structured_output(ResearchResult)

    # System prompt for strict relevance checking
    system_prompt = """You are an advanced AI Research Assistant agent. Your job is to conduct deep research on technical, academic, scientific, or professional topics.

CRITICAL INSTRUCTION ON RELEVANCE:
- Analyze the user's query carefully.
- If the query is completely unrelated to research, science, technology, academic domains, engineering, business analysis, or professional studies (e.g., queries about cooking recipes, sports match live scores, movies, entertainment, personal gossip, casual chit-chat, or random non-academic questions), you MUST set `is_relevant` to `false`.
- If `is_relevant` is `false`, leave `executive_summary_points`, `key_findings`, and `sources` completely empty, and set `topic` to "Irrelevant Query / Out of Domain".
- Only if the query is a valid research/technical/academic topic, set `is_relevant` to `true`, perform a web search if needed, and fill out the detailed executive summary points, key findings, and verified sources.

Past Conversation Context:
{history}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{query}")
    ])

    chain = prompt | structured_llm

    # Format past conversation history
    formatted_history = ""
    if history:
        for h in history:
            formatted_history += f"User Query: {h['query']}\nSummary: {h['summary']}\n---\n"
    else:
        formatted_history = "No previous history."

    # Execute the agent chain
    try:
        result = chain.invoke({
            "history": formatted_history,
            "query": query
        })
        return result
    except Exception as e:
        return ResearchResult(
            is_relevant=False,
            topic="Error Processing Query",
            executive_summary_points=[f"An error occurred: {str(e)}"],
            key_findings=[],
            sources=[]
        )