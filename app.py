import streamlit as st
import os
import json
import asyncio
from pathlib import Path
import tempfile

# Initialize environment for LiteLLM to use Gemini Flash
from dotenv import load_dotenv
load_dotenv()

# Assuming the user provides OPENAI_API_KEY through Streamlit secrets or environment variables
try:
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
except FileNotFoundError:
    pass

from agents import Agent, Runner, function_tool, set_tracing_disabled
from agents.stream_events import RawResponsesStreamEvent, RunItemStreamEvent
from openai.types.responses import ResponseTextDeltaEvent, ResponseReasoningSummaryTextDeltaEvent

from pageindex import PageIndexClient
import pageindex.utils as utils

st.set_page_config(page_title="PageIndex & OpenAI RAG", page_icon="📚", layout="wide")

st.title("📚 Vectorless RAG with PageIndex & OpenAI (gpt-4o-mini)")
st.markdown("Upload a PDF to index it using the PageIndex tree structure, then chat with an agent powered by **OpenAI gpt-4o-mini**.")

WORKSPACE = Path("./workspace")
WORKSPACE.mkdir(exist_ok=True)

@st.cache_resource
def get_client():
    # Pass retrieve_model and model='gpt-4o-mini'
    return PageIndexClient(workspace=WORKSPACE, model="gpt-4o-mini", retrieve_model="gpt-4o-mini")

client = get_client()

AGENT_SYSTEM_PROMPT = """
You are a helpful document QA assistant using PageIndex.
TOOL USE:
- Call get_document() first to confirm status and page/line count.
- Call get_document_structure() to identify relevant page ranges.
- Call get_page_content(pages="5-7") with tight ranges; never fetch the whole document.
Answer based only on tool output. Be concise.
"""

# File Uploader
uploaded_file = st.sidebar.file_uploader("Upload a PDF document", type=["pdf"])

if uploaded_file:
    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    file_path = Path(temp_dir) / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    st.sidebar.success(f"Loaded {uploaded_file.name}")
    
    # Check if we already have it in the workspace
    doc_id = next(
        (did for did, doc in client.documents.items() if doc.get('doc_name') == file_path.name),
        None,
    )
    
    if not doc_id:
        with st.spinner("Indexing PDF... This might take a moment."):
            doc_id = client.index(file_path)
        st.sidebar.success(f"Indexed successfully! ID: {doc_id}")
    else:
        st.sidebar.info(f"Using cached index. ID: {doc_id}")

    # Chat Interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask a question about the document..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            st_callback = st.empty()
            
            # Define tools bound to the current doc_id
            @function_tool
            def get_document() -> str:
                """Get document metadata: status, page count, name, and description."""
                return client.get_document(doc_id)

            @function_tool
            def get_document_structure() -> str:
                """Get the document's full tree structure (without text) to find relevant sections."""
                return client.get_document_structure(doc_id)

            @function_tool
            def get_page_content(pages: str) -> str:
                """
                Get the text content of specific pages or line numbers.
                Use tight ranges: e.g. '5-7' for pages 5 to 7, '3,8' for pages 3 and 8, '12' for page 12.
                """
                return client.get_page_content(doc_id, pages)

            agent = Agent(
                name="PageIndex_Agent",
                instructions=AGENT_SYSTEM_PROMPT,
                tools=[get_document, get_document_structure, get_page_content],
                model="gpt-4o-mini",
            )

            async def _run_stream():
                streamed_run = Runner.run_streamed(agent, prompt)
                full_response = ""
                current_stream_kind = None
                
                async for event in streamed_run.stream_events():
                    if isinstance(event, RawResponsesStreamEvent):
                        if isinstance(event.data, ResponseReasoningSummaryTextDeltaEvent):
                            delta = event.data.delta
                            full_response += delta
                            st_callback.markdown(full_response + "▌")
                        elif isinstance(event.data, ResponseTextDeltaEvent):
                            delta = event.data.delta
                            full_response += delta
                            st_callback.markdown(full_response + "▌")
                    elif isinstance(event, RunItemStreamEvent):
                        item = event.item
                        if item.type == "tool_call_item":
                            raw = item.raw_item
                            args = getattr(raw, "arguments", "{}")
                            full_response += f"\n\n*🔧 Calling tool: `{raw.name}`*\n\n"
                            st_callback.markdown(full_response + "▌")
                
                return full_response

            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                final_answer = loop.run_until_complete(_run_stream())
                st_callback.markdown(final_answer)
                st.session_state.messages.append({"role": "assistant", "content": final_answer})
            except Exception as e:
                st.error(f"Error during agent execution: {e}")

else:
    st.info("Please upload a PDF document in the sidebar to begin.")
