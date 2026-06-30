from typing import Dict, Any
from .base import BaseVoiceProvider

class FasterWhisperProvider(BaseVoiceProvider):
    @property
    def provider_name(self) -> str:
        return "faster_whisper"

    async def transcribe(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        raise NotImplementedError("Local faster-whisper provider not yet implemented.")
