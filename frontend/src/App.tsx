import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';
import { Sidebar } from './components/layout/Sidebar';
import { DocumentUpload } from './pages/DocumentUpload';
import { KnowledgeCapture } from './pages/KnowledgeCapture';
import './App.css';

const Placeholder = ({ title }: { title: string }) => (
  <div className="page-container">
    <h2>{title}</h2>
    <p>This view is under construction.</p>
  </div>
);

const App: React.FC = () => {
  return (
    <AuthProvider>
      <ThemeProvider>
        <BrowserRouter>
          <div className="app-container">
            <Sidebar />
            <main className="main-content">
              <Routes>
                <Route path="/" element={<Navigate to="/documents" />} />
                <Route path="/voice" element={<Placeholder title="Voice Chat" />} />
                <Route path="/capture" element={<KnowledgeCapture />} />
                <Route path="/documents" element={<DocumentUpload />} />
                <Route path="/settings" element={<Placeholder title="Settings" />} />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </ThemeProvider>
    </AuthProvider>
  );
};

export default App;
