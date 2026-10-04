import streamlit as st
from agents import run_research

st.set_page_config(page_title="Agentic AI Research Assistant", page_icon="🔎", layout="wide")
st.title("🔎 Agentic AI Research Assistant")
st.caption("Plan → Research → Analyze → Report")

with st.sidebar:
    st.header("Settings")
    st.info("Add your Gemini API key to the .env file before running.")
    depth=st.selectbox("Research depth", ["Quick", "Standard", "Deep"], index=1)
    st.caption("Deep research uses more search results and Gemini calls.")

topic=st.text_area("What would you like to research?", placeholder="Example: How is generative AI changing healthcare?", height=120)
if st.button("Start research", type="primary", disabled=not topic.strip()):
    with st.spinner("Agents are working through your research..."):
        try:
            result=run_research(topic.strip(), depth)
            st.session_state["research_result"]=result
        except Exception as exc:
            st.error(f"Research failed: {exc}")
            st.stop()

if "research_result" in st.session_state:
    result=st.session_state["research_result"]
    st.subheader("Research plan")
    for i, task in enumerate(result["plan"],1):
        st.write(f"{i}. {task}")
    st.subheader("Final report")
    st.markdown(result["report"])
    with st.expander("Sources gathered"):
        for item in result["sources"]:
            st.markdown(f"- [{item['title']}]({item['url']})")
    st.download_button("Download report", result["report"], file_name="research_report.md", mime="text/markdown")
