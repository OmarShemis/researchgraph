import asyncio
from uuid import uuid4

import streamlit as st

from researchgraph.config import get_model
from researchgraph.graphs.rgraph import build_graph
from researchgraph.integrations.mcp_client import connect_mcp


async def research(messages, status):
    question = "\n\n".join(f"{message['role']}: {message['content']}" for message in messages)
    model = get_model()
    async with connect_mcp() as tools:
        graph = build_graph(model, tools)
        result = {}
        async for update in graph.astream(
            {"question": question},
            config={"configurable": {"thread_id": str(uuid4())}, "recursion_limit": 100},
            stream_mode="updates",
        ):
            for stage, values in update.items():
                result.update(values)
                status.write(f"Completed: {stage.replace('_', ' ')}")
        return result["report"]


st.set_page_config(page_title="ResearchGraph", page_icon="🔎")
st.title("ResearchGraph")
st.caption("Ask a research question or follow up on a previous report.")

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.button("New chat"):
    st.session_state.messages = []
    st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if question := st.chat_input("What would you like to research?"):
    if question.strip():
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            status = st.status("Researching...", expanded=True)
            try:
                report = asyncio.run(research(st.session_state.messages, status))
            except Exception as error:
                status.update(label="Research failed", state="error")
                st.error(f"{error}\n\nCheck that your local model and MCP servers are running.")
            else:
                status.update(label="Research complete", state="complete", expanded=False)
                st.markdown(report)
                st.session_state.messages.append({"role": "assistant", "content": report})
