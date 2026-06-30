from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    llm_reachable: bool
    pageindex_initialized: bool

class ErrorResponse(BaseModel):
    error_code: str = Field(..., description="A standard string code like 'validation_error' or 'not_found'")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional details about the error")

class ChatRequestMetadata(BaseModel):
    user_id: Optional[str] = None
    source: Optional[str] = None
    session_id: Optional[str] = None
    
    class Config:
        extra = "allow" # Allow other random metadata fields if needed

class ChatRequest(BaseModel):
    doc_id: str = Field(..., description="The document ID to query against")
    prompt: str = Field(..., description="The user's query")
    conversation_id: Optional[str] = Field(None, description="Future extension for threaded conversations")
    metadata: Optional[ChatRequestMetadata] = Field(None, description="Optional metadata about the request")

class ChatStreamEvent(BaseModel):
    type: str = Field(..., description="Event type: 'transcript', 'text', 'reasoning', 'tool_call', 'tool_call_output', 'error'")
    delta: Optional[str] = Field(None, description="Text delta content")
    message_id: str = Field(..., description="Unique message ID")
    timestamp: str = Field(..., description="ISO timestamp of the event")
    finished: bool = Field(False, description="True if this is the final event")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Optional data payload, e.g., tool_name or tool_output")

class UploadResponse(BaseModel):
    doc_id: str
    message: str

class TranscriptMetadata(BaseModel):
    transcript: str
    provider: str
    processing_time_ms: float
    detected_language: Optional[str] = None
    audio_duration: Optional[float] = None
    saved_path: Optional[str] = None

class VoiceNoteResponse(BaseModel):
    transcript_metadata: TranscriptMetadata
    summary: str
    action_items: list[str]
    tags: list[str]
