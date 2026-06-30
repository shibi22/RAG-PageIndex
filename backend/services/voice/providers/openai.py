import os
import asyncio
from typing import Dict, Any
from .base import BaseVoiceProvider
from backend.config import settings

class OpenAIProvider(BaseVoiceProvider):
    @property
    def provider_name(self) -> str:
        return "openai"

    async def transcribe(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            with open(file_path, "rb") as audio_file:
                # Whisper API requires a file object
                transcription = await client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    response_format="verbose_json" # Gets language and duration
                )
                
                return {
                    "text": transcription.text,
                    "language": getattr(transcription, "language", "unknown"),
                    "duration": getattr(transcription, "duration", None)
                }
        except Exception as e:
            raise RuntimeError(f"OpenAI Transcription failed: {str(e)}")
