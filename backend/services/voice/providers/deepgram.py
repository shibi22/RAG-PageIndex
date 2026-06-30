from typing import Dict, Any
from .base import BaseVoiceProvider

class DeepgramProvider(BaseVoiceProvider):
    @property
    def provider_name(self) -> str:
        return "deepgram"

    async def transcribe(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        raise NotImplementedError("Deepgram provider not yet implemented.")
