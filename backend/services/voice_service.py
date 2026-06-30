import time
from typing import Dict, Any, Tuple
from fastapi import UploadFile, HTTPException

from .voice.providers.openai import OpenAIProvider
from .transcript_storage import storage
from backend.utils.logging import logger

MAX_FILE_SIZE_MB = 25
SUPPORTED_MIMES = ["audio/mpeg", "audio/mp4", "audio/x-m4a", "audio/wav", "audio/webm", "video/webm"]

# We can dynamically select the provider via config in the future
active_provider = OpenAIProvider()

async def validate_audio(file: UploadFile) -> None:
    """Validates MIME type and size."""
    if file.content_type not in SUPPORTED_MIMES:
        # Some browsers send octet-stream for webm
        if not file.filename.endswith((".webm", ".wav", ".mp3", ".m4a")):
            raise HTTPException(status_code=400, detail=f"Unsupported audio format: {file.content_type}")
    
    # Check size by seeking
    file.file.seek(0, 2)
    size_mb = file.file.tell() / (1024 * 1024)
    file.file.seek(0)
    
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File too large. Max {MAX_FILE_SIZE_MB}MB.")

async def process_voice_input(file: UploadFile, save: bool = True) -> Tuple[str, Dict[str, Any]]:
    """
    Validates, transcribes, and optionally saves the transcript.
    Returns (transcript_text, metadata_dict)
    """
    await validate_audio(file)
    
    # Write to temporary file for the provider
    import tempfile
    import os
    
    start_time = time.time()
    temp_path = os.path.join(tempfile.gettempdir(), file.filename)
    
    try:
        with open(temp_path, "wb") as f:
            f.write(file.file.read())
            
        logger.info(f"Transcribing {file.filename} using {active_provider.provider_name}...")
        result = await active_provider.transcribe(temp_path, file.content_type)
        
        latency = (time.time() - start_time) * 1000
        
        metadata = {
            "provider": active_provider.provider_name,
            "processing_time_ms": latency,
            "language": result.get("language"),
            "duration": result.get("duration"),
            "file_size_bytes": os.path.getsize(temp_path)
        }
        
        logger.info(f"Transcription successful. Latency: {latency:.2f}ms")
        
        if save:
            filepath = storage.save(result["text"], metadata)
            metadata["saved_path"] = filepath
            
        return result["text"], metadata
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

async def generate_knowledge_capture(transcript: str) -> Dict[str, Any]:
    """Uses LLM to summarize and extract action items from a transcript."""
    # We will use LiteLLM or OpenAI client directly since it's a simple prompt
    from openai import AsyncOpenAI
    from backend.config import settings
    import json
    
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    system_prompt = """
    You are a Knowledge Capture assistant. Analyze the given transcript and return a JSON object with:
    - "summary": A concise paragraph summarizing the note.
    - "action_items": A list of strings containing actionable tasks mentioned.
    - "tags": A list of short string tags for categorization.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript}
        ],
        response_format={"type": "json_object"}
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Failed to parse Knowledge Capture JSON: {e}")
        return {"summary": "Failed to generate summary.", "action_items": [], "tags": []}
