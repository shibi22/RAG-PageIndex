from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseVoiceProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the STT provider."""
        pass

    @abstractmethod
    async def transcribe(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        """
        Transcribes the audio file.
        Must return a dict with at least:
        - 'text': The full transcript string
        - 'language': Detected language (optional)
        - 'duration': Duration in seconds (optional)
        """
        pass
