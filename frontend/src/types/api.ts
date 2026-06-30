export interface ChatStreamEvent {
  type: 'transcript' | 'text' | 'reasoning' | 'tool_call' | 'tool_call_output' | 'error' | 'finished';
  delta?: string;
  message_id: string;
  timestamp: string;
  finished: boolean;
  additional_data?: any;
}
export interface UploadResponse {
  doc_id: string;
  message: string;
}
export interface TranscriptMetadata {
  transcript: string;
  provider: string;
  processing_time_ms: number;
  detected_language?: string;
  audio_duration?: number;
}
export interface VoiceNoteResponse {
  transcript_metadata: TranscriptMetadata;
  summary: string;
  action_items: string[];
  tags: string[];
}
