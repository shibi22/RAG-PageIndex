import React, { useState, useRef } from 'react';
import { Mic, Square, Download } from 'lucide-react';
import { voiceApi } from '../api/voiceApi';
import type { VoiceNoteResponse } from '../types/api';

export const KnowledgeCapture: React.FC = () => {
  const [recording, setRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VoiceNoteResponse | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorderRef.current = new MediaRecorder(stream);
    
    mediaRecorderRef.current.ondataavailable = e => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    
    mediaRecorderRef.current.onstop = async () => {
      const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
      chunksRef.current = [];
      setLoading(true);
      try {
        const res = await voiceApi.note(audioBlob, 'capture.webm');
        setResult(res);
      } catch (e) {
        alert('Capture failed.');
      } finally {
        setLoading(false);
      }
    };
    
    mediaRecorderRef.current.start();
    setRecording(true);
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current?.stream.getTracks().forEach(t => t.stop());
    setRecording(false);
  };

  return (
    <div className="page-container">
      <h2>Knowledge Capture</h2>
      <div className="card" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
        <button 
          className="btn" 
          style={{ borderRadius: '50%', width: '80px', height: '80px', justifyContent: 'center', backgroundColor: recording ? '#ef4444' : 'var(--primary-color)' }}
          onClick={recording ? stopRecording : startRecording}
          disabled={loading}
        >
          {recording ? <Square size={32} /> : <Mic size={32} />}
        </button>
        <p style={{ marginTop: '1rem', color: 'var(--text-color)' }}>
          {recording ? 'Recording... Tap to stop' : loading ? 'Processing AI Knowledge...' : 'Tap to Record a Note'}
        </p>
      </div>
      
      {result && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>Captured Knowledge</h3>
            <button className="btn btn-secondary"><Download size={16} /> Export</button>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            {result.tags.map(t => <span key={t} style={{background: 'var(--primary-color)', color: 'white', padding: '0.25rem 0.5rem', borderRadius: '1rem', fontSize: '0.8rem'}}>{t}</span>)}
          </div>
          <h4>Summary</h4>
          <p>{result.summary}</p>
          <h4>Action Items</h4>
          <ul>
            {result.action_items.map((item, i) => <li key={i}>{item}</li>)}
          </ul>
          <h4>Transcript</h4>
          <p style={{ color: 'gray', fontSize: '0.9rem' }}>{result.transcript_metadata.transcript}</p>
        </div>
      )}
    </div>
  );
};
