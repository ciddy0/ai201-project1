"""
app.py — Streamlit interface for the CSULB CS Professor Unofficial Guide.

Run with: streamlit run app.py
"""

import streamlit as st
from rag import build_vector_store, ask

st.set_page_config(page_title="CSULB CS Professor Guide")


@st.cache_resource(show_spinner="Loading vector store...")
def init_vector_store():
    return build_vector_store()


# One-time initialization
init_vector_store()

st.title("CSULB CS Professor Guide")
st.caption("Ask anything about CS professors and courses at CSULB, based on real student reviews.")

query = st.text_input("Ask a question", placeholder="e.g. How heavy is the workload for Neal Terrel's classes?")

if query:
    with st.spinner("Searching reviews and generating answer..."):
        result = ask(query)

    st.markdown("### Answer")
    st.markdown(result["answer"])

    if result["sources"]:
        st.markdown("### Sources")
        for src in result["sources"]:
            label = f"{src['source_type'].upper()} — {src['professor']}"
            st.markdown(f"- [{label}]({src['url']})")
