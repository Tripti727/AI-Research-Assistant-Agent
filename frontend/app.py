import sys
import os
import json
import io

d = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(d))

import streamlit as st
from backend.agent_logic import run_research_agent
from backend.database import SessionLocal, init_db, ResearchHistoryModel
from backend.models import ResearchResult, ResearchSource

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

init_db()

st.set_page_config(page_title="AI Research Assistant", page_icon="🔬", layout="wide")

st.title("🔬 AI Research Assistant Agent")
st.write("Powered by LangChain, Groq LLM & SQLite Database")

def create_pdf(topic, summary_points, key_findings, sources):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('ReportTitle', parent=styles['Heading1'], fontSize=18, textColor='#1f4e79', spaceAfter=12)
    heading_style = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=14, textColor='#2c3e50', spaceBefore=10, spaceAfter=6)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, textColor='#333333', spaceAfter=6)
    
    story.append(Paragraph(f"Research Report: {topic}", title_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Executive Summary", heading_style))
    for pt in summary_points:
        story.append(Paragraph(f"• {pt}", body_style))
    
    if key_findings:
        story.append(Spacer(1, 8))
        story.append(Paragraph("Key Findings", heading_style))
        for kf in key_findings:
            story.append(Paragraph(f"• {kf}", body_style))
            
    if sources:
        story.append(Spacer(1, 8))
        story.append(Paragraph("Sources & References", heading_style))
        for src in sources:
            story.append(Paragraph(f"• <a href='{src.url}'>{src.title}</a> ({src.url})", body_style))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

db = SessionLocal()
saved_records = db.query(ResearchHistoryModel).all()
db.close()

st.sidebar.header("📜 Search History")
if st.sidebar.button("Clear Current View"):
    st.session_state.chat_history = []
    st.rerun()

st.sidebar.markdown("---")
if saved_records:
    for rec in saved_records:
        if st.sidebar.button(f"🔍 {rec.query}", key=f"db_hist_{rec.id}"):
            try:
                summary_list = json.loads(rec.executive_summary) if rec.executive_summary else [rec.summary]
            except:
                summary_list = [rec.summary] if rec.summary else []

            try:
                findings_list = json.loads(rec.key_findings) if rec.key_findings else []
            except:
                findings_list = []

            sources_list = json.loads(rec.sources) if rec.sources else []

            # CRITICAL FIX: Explicitly check if topic indicates an irrelevant query
            is_rel = False if rec.topic == "Irrelevant Query / Out of Domain" else True

            res_obj = ResearchResult(
                is_relevant=is_rel,
                topic=rec.topic,
                executive_summary_points=summary_list,
                key_findings=findings_list,
                sources=[ResearchSource(**s) for s in sources_list]
            )
            st.session_state.chat_history = [{"q": rec.query, "res": res_obj}]
            st.rerun()

for i, c in enumerate(st.session_state.chat_history):
    with st.chat_message("user"):
        st.write(c["q"])

    with st.chat_message("assistant"):
        with st.container(border=True):
            # Check if query is relevant right at the top
            if not c["res"].is_relevant:
                st.warning("⚠️ **Polite Refusal:** This topic is not related to research, science, technology, or academic domains. Please enter a valid research or technical query.")
            else:
                st.markdown("### 📄 EXECUTIVE RESEARCH REPORT")
                st.markdown(f"**Topic:** {c['res'].topic}")
                st.markdown("---")
                
                st.markdown("#### 📌 Executive Summary")
                for pt in c["res"].executive_summary_points:
                    st.markdown(f"- {pt}")
                    
                if c["res"].key_findings:
                    st.markdown("#### 💡 Key Technical Findings")
                    for kf in c["res"].key_findings:
                        st.markdown(f"* {kf}")
                        
                if c["res"].sources or c["res"].executive_summary_points:
                    st.markdown("---")
                    pdf_bytes = create_pdf(
                        topic=c['res'].topic,
                        summary_points=c['res'].executive_summary_points,
                        key_findings=c['res'].key_findings,
                        sources=c['res'].sources
                    )
                    
                    col_dl, col_info = st.columns([1, 2])
                    with col_dl:
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_bytes,
                            file_name=f"research_report_{i+1}.pdf",
                            mime="application/pdf",
                            key=f"download_btn_{i}"
                        )
                    with col_info:
                        st.caption("✨ Ready-to-share certified technical brief.")

                if c["res"].sources:
                    st.markdown("---")
                    st.markdown("#### 🔗 Verified Sources & References")
                    for src in c["res"].sources:
                        st.markdown(f"- [{src.title}]({src.url})")

st.markdown("---")
with st.form(key="my_form", clear_on_submit=True):
    user_input = st.text_area("Research Topic:", height=80, placeholder="Enter a technical or research-related topic...")
    btn = st.form_submit_button("Search", type="primary")

if btn:
    if not user_input.strip():
        st.warning("Please enter something!")
    else:
        with st.spinner("Analyzing query relevance & searching via LangChain..."):
            try:
                past_data = []
                for item in st.session_state.chat_history:
                    sum_text = " ".join(item["res"].executive_summary_points)
                    past_data.append({"query": item["q"], "summary": sum_text})
                
                res = run_research_agent(query=user_input, history=past_data)
                
                db_session = SessionLocal()
                summary_json = json.dumps(res.executive_summary_points)
                findings_json = json.dumps(res.key_findings)
                sources_json = json.dumps([s.dict() for s in res.sources])
                
                db_item = ResearchHistoryModel(
                    query=user_input,
                    topic=res.topic,
                    executive_summary=summary_json,
                    key_findings=findings_json,
                    sources=sources_json
                )
                db_session.add(db_item)
                db_session.commit()
                db_session.close()
                
                st.session_state.chat_history.append({"q": user_input, "res": res})
                st.rerun()
            except Exception as ex:
                st.error(f"Error: {ex}")