import React, { useState } from 'react';
import { uploadApi } from '../api/uploadApi';

export const DocumentUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [docId, setDocId] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const res = await uploadApi.uploadDocument(file);
      setDocId(res.doc_id);
      localStorage.setItem('activeDocId', res.doc_id);
      alert(`Indexed successfully! ID: ${res.doc_id}`);
    } catch (e) {
      alert('Upload failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <h2>Document Upload</h2>
      <div className="card">
        <p>Upload a PDF to start chatting or capturing knowledge.</p>
        <input type="file" accept=".pdf" onChange={e => setFile(e.target.files?.[0] || null)} />
        <br/><br/>
        <button className="btn" onClick={handleUpload} disabled={!file || loading}>
          {loading ? 'Uploading...' : 'Upload & Index'}
        </button>
        {docId && <p style={{marginTop: '1rem', color: 'green'}}>Active Document: {docId}</p>}
      </div>
    </div>
  );
};
