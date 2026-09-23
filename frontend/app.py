import sys
import os

d = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(d))

import streamlit as st
from backend.agent_logic import run_research_agent

st.set_page_config(page_title="Research Agent", page_icon="🔬", layout="wide")

st.title("🔬 AI Research Assistant Agent")
st.write("Enter your topic below to get summarized research reports.")

if "history" not in st.session_state:
    st.session_state.history = []

if "edit_box" not in st.session_state:
    st.session_state.edit_box = ""

st.sidebar.header("Controls")
if st.sidebar.button("Clear Chat"):
    st.session_state.history = []
    st.session_state.edit_box = ""
    st.rerun()

st.sidebar.markdown("---")
if st.session_state.history:
    st.sidebar.subheader("Past Queries")
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
        with st.spinner("Searching web..."):
            try:
                past_data = []
                for item in st.session_state.history:
                    sum_text = " ".join(item["res"].executive_summary_points)
                    past_data.append({"query": item["q"], "summary": sum_text})
                
                res = run_research_agent(query=user_input, history=past_data)
                st.session_state.history.append({"q": user_input, "res": res})
                st.session_state.edit_box = ""
                st.rerun()
            except Exception as ex:
                st.error(f"Error: {ex}")