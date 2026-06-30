import React from 'react';
import { NavLink } from 'react-router-dom';
import { MessageSquare, Mic, FileText, Upload, Settings, BookOpen } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

export const Sidebar: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <BookOpen className="text-primary" /> PageIndex AI
      </div>
      
      <nav className="sidebar-nav">
        <NavLink to="/" className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`} end>
          <MessageSquare size={18} /> <span>Chat</span>
        </NavLink>
        <NavLink to="/voice" className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`}>
          <Mic size={18} /> <span>Voice Chat</span>
        </NavLink>
        <NavLink to="/capture" className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`}>
          <FileText size={18} /> <span>Knowledge Capture</span>
        </NavLink>
        <NavLink to="/documents" className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`}>
          <Upload size={18} /> <span>Documents</span>
        </NavLink>
        <NavLink to="/settings" className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`}>
          <Settings size={18} /> <span>Settings</span>
        </NavLink>
      </nav>

      <div style={{ marginTop: 'auto' }}>
        <button className="btn btn-secondary" onClick={toggleTheme} style={{ width: '100%' }}>
          Toggle {theme === 'light' ? 'Dark' : 'Light'} Mode
        </button>
      </div>
    </aside>
  );
};
