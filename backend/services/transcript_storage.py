import os
import uuid
import datetime
from typing import Dict, Any
from backend.config import settings

class TranscriptStorage:
    def __init__(self):
        self.storage_dir = os.path.join(settings.WORKSPACE_DIR, "transcripts")
        os.makedirs(self.storage_dir, exist_ok=True)
        
    def save(self, text: str, metadata: Dict[str, Any]) -> str:
        """Saves transcript to local storage for future indexing and returns the filepath."""
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        uid = str(uuid.uuid4())[:8]
        filename = f"transcript_{timestamp}_{uid}.md"
        filepath = os.path.join(self.storage_dir, filename)
        
        # Build Markdown content
        content = f"# Voice Transcript: {timestamp}\n\n"
        content += f"**Provider**: {metadata.get('provider', 'unknown')}\n"
        content += f"**Duration**: {metadata.get('duration', 'unknown')}s\n"
        content += f"**Language**: {metadata.get('language', 'unknown')}\n"
        content += "\n## Transcript\n\n"
        content += text
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        return filepath

# Singleton instance
storage = TranscriptStorage()
