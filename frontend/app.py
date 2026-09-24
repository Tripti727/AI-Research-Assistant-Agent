import sys
import os
import json

d = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(d))

import streamlit as st
from backend.agent_logic import run_research_agent
from backend.database import SessionLocal, init_db, ResearchHistoryModel
from backend.models import ResearchResult, ResearchSource

init_db()

st.set_page_config(page_title="Research Agent", page_icon="🔬", layout="wide")

st.title("🔬 AI Research Assistant Agent")
st.write("Powered by Groq LLM & SQLite Database")

if "history" not in st.session_state:
    db = SessionLocal()
    saved_records = db.query(ResearchHistoryModel).all()
    st.session_state.history = []
    for rec in saved_records:
        sources_list = json.loads(rec.sources) if rec.sources else []
        res_obj = ResearchResult(
            is_relevant=True,
            topic=rec.topic,
            executive_summary_points=[rec.summary],
            key_findings=[],
            sources=[ResearchSource(**s) for s in sources_list]
        )
        st.session_state.history.append({"q": rec.query, "res": res_obj})
    db.close()

if "edit_box" not in st.session_state:
    st.session_state.edit_box = ""

st.sidebar.header("Controls")
if st.sidebar.button("Clear Chat Session"):
    st.session_state.history = []
    st.session_state.edit_box = ""
    st.rerun()

st.sidebar.markdown("---")
if st.session_state.history:
    st.sidebar.subheader("Saved Queries (DB)")
    for i, c in enumerate(st.session_state.history):
        st.sidebar.text(f"{i+1}. {c['q'][:25]}...")

for i, c in enumerate(st.session_state.history):
    with st.chat_message("user"):
        col1, col2 = st.columns([10, 1])
        with col1:
            st.write(c["q"])
        with col2:
            if st.button("✏️", key=f"e_{i}"):
                st.session_state.edit_box = c["q"]
                st.session_state.history = st.session_state.history[:i]
                st.rerun()

    with st.chat_message("assistant"):
        st.markdown(f"### Report: {c['res'].topic}")
        st.markdown("#### Summary")
        for pt in c["res"].executive_summary_points:
            st.markdown(f"- {pt}")
            
        if c["res"].key_findings:
            st.markdown("#### Key Findings")
            for kf in c["res"].key_findings:
                st.markdown(f"* {kf}")
                
        if c["res"].sources:
            st.markdown("#### Sources")
            for src in c["res"].sources:
                st.markdown(f"- [{src.title}]({src.url})")

st.markdown("---")
with st.form(key="my_form", clear_on_submit=True):
    user_input = st.text_area("Research Topic:", value=st.session_state.edit_box, height=80)
    btn = st.form_submit_button("Search", type="primary")

if btn:
    if not user_input.strip():
        st.warning("Please enter something!")
    else:
        with st.spinner("Searching web & saving to database..."):
            try:
                past_data = []
                for item in st.session_state.history:
                    sum_text = " ".join(item["res"].executive_summary_points)
                    past_data.append({"query": item["q"], "summary": sum_text})
                
                res = run_research_agent(query=user_input, history=past_data)
                
                db = SessionLocal()
                summary_text = " ".join(res.executive_summary_points)
                sources_json = json.dumps([s.dict() for s in res.sources])
                db_item = ResearchHistoryModel(
                    query=user_input,
                    topic=res.topic,
                    summary=summary_text,
                    sources=sources_json
                )
                db.add(db_item)
                db.commit()
                db.close()
                
                st.session_state.history.append({"q": user_input, "res": res})
                st.session_state.edit_box = ""
                st.rerun()
            except Exception as ex:
                st.error(f"Error: {ex}")