import { apiClient } from './client';
import type { TranscriptMetadata, VoiceNoteResponse } from '../types/api';

export const voiceApi = {
  transcribe: async (audioBlob: Blob, filename: string): Promise<TranscriptMetadata> => {
    const formData = new FormData();
    formData.append('file', audioBlob, filename);
    const res = await apiClient.post<TranscriptMetadata>('/voice/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  note: async (audioBlob: Blob, filename: string): Promise<VoiceNoteResponse> => {
    const formData = new FormData();
    formData.append('file', audioBlob, filename);
    const res = await apiClient.post<VoiceNoteResponse>('/voice/note', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  }
};
