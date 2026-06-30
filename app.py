import streamlit as st
import requests
import json
import tempfile
import time
from pathlib import Path

# Config
API_BASE_URL = "http://127.0.0.1:8000/api/v1"

st.set_page_config(page_title="Voice AI Knowledge Assistant", page_icon="📚", layout="wide")

st.title("📚 Vectorless RAG with PageIndex (FastAPI Backend)")
st.markdown("Upload a PDF to index it, then chat with the agent powered by the new FastAPI backend.")

# Check API Health
try:
    health = requests.get(f"{API_BASE_URL}/health", timeout=2).json()
    if health.get("status") == "ok":
        st.sidebar.success("✅ Backend API is online")
    else:
        st.sidebar.warning("⚠️ Backend API health check failed")
except Exception:
    st.sidebar.error("❌ Backend API is offline. Ensure `uvicorn backend.main:app` is running.")
    st.stop()

# File Uploader
uploaded_file = st.sidebar.file_uploader("Upload a PDF document", type=["pdf"])

if "doc_id" not in st.session_state:
    st.session_state.doc_id = None

if uploaded_file:
    # Check if this is a new file we need to upload
    if st.session_state.get("last_uploaded_name") != uploaded_file.name:
        with st.spinner("Uploading and indexing PDF..."):
            try:
                # Send to FastAPI upload endpoint
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                response = requests.post(f"{API_BASE_URL}/upload", files=files)
                response.raise_for_status()
                
                result = response.json()
                st.session_state.doc_id = result["doc_id"]
                st.session_state.last_uploaded_name = uploaded_file.name
                
                # Clear chat history on new document
                st.session_state.messages = []
                st.sidebar.success(f"Indexed successfully! ID: {result['doc_id']}")
            except requests.exceptions.RequestException as e:
                st.sidebar.error(f"Failed to upload document: {e}")
                
    else:
        st.sidebar.info(f"Using active document ID: {st.session_state.doc_id}")

# Chat Interface
if st.session_state.doc_id:
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
            full_response = ""
            
            payload = {
                "doc_id": st.session_state.doc_id,
                "prompt": prompt,
                "metadata": {"source": "streamlit"}
            }
            
            try:
                # Stream the response from the backend
                with requests.post(f"{API_BASE_URL}/chat", json=payload, stream=True) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith('data: '):
                                event_data = json.loads(decoded_line[6:])
                                
                                if event_data.get("type") in ["text", "reasoning"] and event_data.get("delta"):
                                    full_response += event_data["delta"]
                                    st_callback.markdown(full_response + "▌")
                                elif event_data.get("type") == "tool_call":
                                    tool_name = event_data.get("additional_data", {}).get("name", "tool")
                                    full_response += f"\n\n*🔧 Calling tool: `{tool_name}`*\n\n"
                                    st_callback.markdown(full_response + "▌")
                                elif event_data.get("type") == "error":
                                    err_msg = event_data.get("additional_data", {}).get("error", "Unknown error")
                                    st.error(f"Backend Error: {err_msg}")
                                    break
                
                st_callback.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Error communicating with backend: {e}")
else:
    st.info("Please upload a PDF document in the sidebar to begin.")
