import { useState, useEffect } from 'react';
import Login from './components/Login';
import Sidebar from './components/Sidebar';
import FileUpload from './components/FileUpload';
import ChatInterface from './components/ChatInterface';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [sessions, setSessions] = useState([{ id: 'default', name: 'General Chat' }]);
  const [currentSessionId, setCurrentSessionId] = useState('default');
  const [view, setView] = useState('chat'); // 'chat' or 'upload'

  useEffect(() => {
    // If token changes, update localStorage
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }, [token]);


  const handleLogout = () => {
    setToken(null);
  };

  const handleNewChat = () => {
    const newId = `session_${Date.now()}`;
    setSessions(prev => [{ id: newId, name: 'New Conversation' }, ...prev]);
    setCurrentSessionId(newId);
    setView('chat');
  };

  return (
    <div className="flex h-screen bg-dark-900 text-slate-200 overflow-hidden font-sans">
      <Sidebar 
        onLogout={handleLogout} 
        onNewChat={handleNewChat}
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={(id) => {
          setCurrentSessionId(id);
          setView('chat');
        }}
      />
      
      <main className="flex-1 flex flex-col relative">
        {/* Top Header */}
        <header className="h-16 border-b border-dark-700 bg-dark-900/80 backdrop-blur-md flex items-center justify-between px-6 z-10">
          <h1 className="font-semibold text-lg">
            {view === 'chat' ? 'Conversation' : 'Knowledge Base Upload'}
          </h1>
          <div className="flex bg-dark-800 p-1 rounded-lg">
            <button 
              onClick={() => setView('chat')}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                view === 'chat' ? 'bg-primary-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Chat
            </button>
            <button 
              onClick={() => setView('upload')}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                view === 'upload' ? 'bg-primary-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Upload
            </button>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden relative">
          <div className={`absolute inset-0 ${view === 'chat' ? 'flex flex-col' : 'hidden'}`}>
            <ChatInterface token={token} sessionId={currentSessionId} />
          </div>
          
          <div className={`absolute inset-0 overflow-y-auto p-6 flex flex-col pt-12 bg-dark-900 ${view === 'upload' ? 'flex' : 'hidden'}`}>
            <div className="text-center mb-8 animate-fade-in-up">
              <h2 className="text-3xl font-bold text-white mb-2">Enhance Knowledge Base</h2>
              <p className="text-slate-400">Upload PDF documents to expand the AI's understanding.</p>
            </div>
            <FileUpload token={token} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
