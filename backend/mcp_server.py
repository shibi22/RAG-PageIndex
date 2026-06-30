import os
import glob
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any

from backend.config import settings
from backend.services.document_service import index_document, check_doc_exists
from backend.services.chat_service import stream_chat_events

# Create the FastMCP server
mcp = FastMCP("KnowledgePlatform")

# --- TOOLS ---

@mcp.tool()
def upload_document(file_path: str) -> str:
    """
    Uploads and indexes a PDF document into the PageIndex knowledge base.
    Args:
        file_path: The absolute path to the local PDF file.
    """
    if not os.path.exists(file_path):
        return f"Error: File {file_path} not found."
    if not file_path.endswith(".pdf"):
        return "Error: Only PDF files are supported."
    
    doc_id = index_document(file_path)
    return f"Successfully indexed document. Document ID: {doc_id}"

@mcp.tool()
def list_documents() -> str:
    """Lists all currently indexed documents in the workspace."""
    workspace = settings.WORKSPACE_DIR
    files = glob.glob(os.path.join(workspace, "*.pdf"))
    if not files:
        return "No documents indexed."
    
    result = "Indexed Documents:\n"
    for f in files:
        result += f"- {os.path.basename(f)}\n"
    return result

@mcp.tool()
async def ask_knowledge_base(doc_id: str, query: str) -> str:
    """
    Queries the knowledge base for a specific document and returns the AI response.
    Args:
        doc_id: The document filename/ID (e.g., 'document.pdf')
        query: The user's question.
    """
    if not check_doc_exists(doc_id):
        return f"Error: Document {doc_id} not found."
    
    full_response = ""
    async for event in stream_chat_events(doc_id, query):
        if event.get("type") in ["text", "reasoning"]:
            full_response += event.get("delta", "")
    
    return full_response

@mcp.tool()
async def capture_knowledge(file_path: str) -> str:
    """
    Extracts knowledge from an audio note (transcribes, summarizes, tags).
    Args:
        file_path: The absolute path to the audio file.
    """
    from backend.services.voice_service import active_provider, generate_knowledge_capture
    from backend.services.transcript_storage import storage
    
    if not os.path.exists(file_path):
        return f"Error: File {file_path} not found."
        
    try:
        # 1. Transcribe
        result = await active_provider.transcribe(file_path, "audio/wav")
        transcript = result["text"]
        
        # 2. Extract Knowledge
        capture_data = await generate_knowledge_capture(transcript)
        
        # 3. Save
        metadata = {"provider": active_provider.provider_name}
        storage.save(transcript, metadata)
        
        output = "Knowledge Capture Successful!\n\n"
        output += f"Summary: {capture_data.get('summary')}\n"
        output += f"Tags: {', '.join(capture_data.get('tags', []))}\n"
        output += "Action Items:\n"
        for item in capture_data.get("action_items", []):
            output += f"- {item}\n"
        return output
        
    except Exception as e:
        return f"Error capturing knowledge: {str(e)}"


# --- RESOURCES ---

@mcp.resource("knowledge://documents/{filename}")
def read_document(filename: str) -> str:
    """Provides direct raw text access to an indexed document."""
    # Since PageIndex stores embeddings, we'll just read the raw PDF text for the resource if possible.
    # In a real scenario, this might return the markdown conversion.
    return f"Raw content access for {filename} is a placeholder. It requires PDF parsing library here."

@mcp.resource("knowledge://notes/{filename}")
def read_voice_note(filename: str) -> str:
    """Provides direct access to a saved voice note transcript."""
    filepath = os.path.join(settings.WORKSPACE_DIR, "transcripts", filename)
    if not os.path.exists(filepath):
        return f"Note {filename} not found."
        
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


# --- PROMPTS ---

@mcp.prompt()
def summarize_meeting(transcript: str) -> str:
    """A workflow to generate a professional meeting summary from a transcript."""
    return f"""Please summarize the following meeting transcript. 
Extract the key decisions made and format them as bullet points. 
Also, highlight any blockers or risks mentioned.

Transcript:
{transcript}
"""

@mcp.prompt()
def explain_like_im_five(topic: str) -> str:
    """A workflow to explain complex topics simply."""
    return f"""Please explain the following topic as if I am 5 years old. 
Use analogies and avoid complex jargon.

Topic:
{topic}
"""

if __name__ == "__main__":
    mcp.run()
