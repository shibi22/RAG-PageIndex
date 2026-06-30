import os
import time
import json
import uuid
import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

from backend.config import settings
from backend.models.schemas import HealthResponse, ChatRequest, UploadResponse, ChatStreamEvent
from backend.services.document_service import index_document, check_doc_exists
from backend.services.chat_service import stream_chat_events
from backend.utils.logging import logger

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    # LLM Reachability check can be expanded to do a ping in the future
    # For now, we assume it's reachable if OPENAI_API_KEY is present
    llm_reachable = bool(settings.OPENAI_API_KEY)
    
    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        llm_reachable=llm_reachable,
        pageindex_initialized=True
    )

@router.post("/upload", response_model=UploadResponse)
def upload_document(file: UploadFile = File(...)):
    """Uploads a PDF, saves it temporarily, and indexes it via PageIndex."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    temp_path = os.path.join(settings.WORKSPACE_DIR, file.filename)
    try:
        with open(temp_path, "wb") as f:
            f.write(file.file.read())
            
        logger.info(f"Indexing document {file.filename}")
        doc_id = index_document(temp_path)
        logger.info(f"Document indexed with ID: {doc_id}")
        
        return UploadResponse(doc_id=doc_id, message="Indexing complete")
    except Exception as e:
        logger.error(f"Failed to index document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Initiates a chat stream for a given document.
    Returns SSE stream of ChatStreamEvent objects.
    """
    if not check_doc_exists(request.doc_id):
        raise HTTPException(status_code=404, detail=f"Document {request.doc_id} not found.")

    logger.info(f"Starting chat stream for doc_id={request.doc_id} with conversation_id={request.conversation_id}")
    message_id = str(uuid.uuid4())

    async def sse_generator():
        try:
            async for raw_event in stream_chat_events(request.doc_id, request.prompt):
                timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
                
                # Transform raw backend event into standardized API event
                event_type = raw_event.get("type", "unknown")
                delta = raw_event.get("delta")
                
                additional_data = {}
                if event_type == "tool_call":
                    additional_data = {"name": raw_event.get("name"), "arguments": raw_event.get("arguments")}
                elif event_type == "tool_call_output":
                    additional_data = {"output": raw_event.get("output")}
                
                stream_event = ChatStreamEvent(
                    type=event_type,
                    delta=delta,
                    message_id=message_id,
                    timestamp=timestamp,
                    finished=False,
                    additional_data=additional_data if additional_data else None
                )
                
                # Yield formatted SSE payload
                yield f"data: {stream_event.model_dump_json(exclude_none=True)}\n\n"
            
            # Send completion event
            final_event = ChatStreamEvent(
                type="finished",
                message_id=message_id,
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                finished=True
            )
            yield f"data: {final_event.model_dump_json(exclude_none=True)}\n\n"
            
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            error_event = ChatStreamEvent(
                type="error",
                message_id=message_id,
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                finished=True,
                additional_data={"error": str(e)}
            )
            yield f"data: {error_event.model_dump_json(exclude_none=True)}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

from backend.services.voice_service import process_voice_input, generate_knowledge_capture
from backend.models.schemas import TranscriptMetadata, VoiceNoteResponse
from fastapi import Form

@router.post("/voice/transcribe", response_model=TranscriptMetadata)
async def voice_transcribe(file: UploadFile = File(...)):
    """Transcribes audio without RAG processing."""
    transcript_text, metadata = await process_voice_input(file, save=False)
    
    return TranscriptMetadata(
        transcript=transcript_text,
        provider=metadata["provider"],
        processing_time_ms=metadata["processing_time_ms"],
        detected_language=metadata.get("language"),
        audio_duration=metadata.get("duration"),
        saved_path=metadata.get("saved_path")
    )

@router.post("/voice/chat")
async def voice_chat(
    file: UploadFile = File(...), 
    doc_id: str = Form(...),
    conversation_id: str = Form(None)
):
    """Transcribes audio, saves it, and streams the RAG response via SSE."""
    if not check_doc_exists(doc_id):
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")

    logger.info(f"Starting voice chat stream for doc_id={doc_id}")
    message_id = str(uuid.uuid4())

    async def sse_voice_generator():
        try:
            # 1. Transcribe Audio
            transcript_text, metadata = await process_voice_input(file, save=True)
            
            # 2. Yield initial transcript event
            transcript_event = ChatStreamEvent(
                type="transcript",
                delta=transcript_text,
                message_id=message_id,
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                finished=False,
                additional_data={"metadata": metadata}
            )
            yield f"data: {transcript_event.model_dump_json(exclude_none=True)}\n\n"
            
            # 3. Stream Chat Events
            async for raw_event in stream_chat_events(doc_id, transcript_text):
                timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
                event_type = raw_event.get("type", "unknown")
                delta = raw_event.get("delta")
                
                additional_data = {}
                if event_type == "tool_call":
                    additional_data = {"name": raw_event.get("name"), "arguments": raw_event.get("arguments")}
                elif event_type == "tool_call_output":
                    additional_data = {"output": raw_event.get("output")}
                
                stream_event = ChatStreamEvent(
                    type=event_type,
                    delta=delta,
                    message_id=message_id,
                    timestamp=timestamp,
                    finished=False,
                    additional_data=additional_data if additional_data else None
                )
                yield f"data: {stream_event.model_dump_json(exclude_none=True)}\n\n"
            
            # 4. Final event
            final_event = ChatStreamEvent(
                type="finished",
                message_id=message_id,
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                finished=True
            )
            yield f"data: {final_event.model_dump_json(exclude_none=True)}\n\n"
            
        except Exception as e:
            logger.error(f"Error during voice streaming: {e}", exc_info=True)
            error_event = ChatStreamEvent(
                type="error",
                message_id=message_id,
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                finished=True,
                additional_data={"error": str(e)}
            )
            yield f"data: {error_event.model_dump_json(exclude_none=True)}\n\n"

    return StreamingResponse(sse_voice_generator(), media_type="text/event-stream")

@router.post("/voice/note", response_model=VoiceNoteResponse)
async def voice_note(file: UploadFile = File(...)):
    """Knowledge Capture: Transcribes, summarizes, extracts action items, and saves."""
    transcript_text, metadata = await process_voice_input(file, save=True)
    
    # Process with LLM
    logger.info(f"Generating Knowledge Capture for {metadata.get('saved_path')}")
    capture_data = await generate_knowledge_capture(transcript_text)
    
    transcript_meta = TranscriptMetadata(
        transcript=transcript_text,
        provider=metadata["provider"],
        processing_time_ms=metadata["processing_time_ms"],
        detected_language=metadata.get("language"),
        audio_duration=metadata.get("duration"),
        saved_path=metadata.get("saved_path")
    )
    
    return VoiceNoteResponse(
        transcript_metadata=transcript_meta,
        summary=capture_data.get("summary", ""),
        action_items=capture_data.get("action_items", []),
        tags=capture_data.get("tags", [])
    )
