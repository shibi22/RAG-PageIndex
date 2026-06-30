import os
from pathlib import Path
from pageindex import PageIndexClient

WORKSPACE_DIR = Path("./workspace")
WORKSPACE_DIR.mkdir(exist_ok=True)

# Default to gpt-4o-mini as set up in the Streamlit app
# Assuming OPENAI_API_KEY is available in the environment
_client = PageIndexClient(
    workspace=WORKSPACE_DIR,
    model="gpt-4o-mini",
    retrieve_model="gpt-4o-mini"
)

def index_document(file_path: str) -> str:
    """
    Index a PDF or Markdown document into the PageIndex knowledge base.
    Returns the doc_id.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    return _client.index(file_path)

def get_document_metadata(doc_id: str) -> str:
    """Get document metadata: status, page count, name, and description."""
    return _client.get_document(doc_id)

def get_document_structure(doc_id: str) -> str:
    """Get the document's full tree structure (without text) to find relevant sections."""
    return _client.get_document_structure(doc_id)

def get_page_content(doc_id: str, pages: str) -> str:
    """
    Get the text content of specific pages or line numbers.
    Use tight ranges: e.g. '5-7' for pages 5 to 7, '3,8' for pages 3 and 8, '12' for page 12.
    """
    return _client.get_page_content(doc_id, pages)

def check_doc_exists(doc_id: str) -> bool:
    """Check if a document exists in the workspace."""
    return doc_id in _client.documents
