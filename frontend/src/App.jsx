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
        <header className="h-20 border-b border-white/5 bg-dark-900/40 backdrop-blur-xl flex items-center justify-between px-8 z-10 shadow-sm relative">
          <div className="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-transparent opacity-50 pointer-events-none"></div>
          
          <div className="flex items-center gap-3 relative z-10">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center shadow-[0_0_15px_rgba(139,92,246,0.4)]">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-white"><path d="M12 2v20"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
            </div>
            <h1 className="font-display font-bold text-2xl tracking-tight text-gradient">
              {view === 'chat' ? 'Nexus AI Assistant' : 'Knowledge Base Upload'}
            </h1>
          </div>

          <div className="flex bg-dark-800/80 p-1.5 rounded-xl border border-white/5 backdrop-blur-md relative z-10">
            <button 
              onClick={() => setView('chat')}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                view === 'chat' ? 'bg-primary-600 text-white shadow-[0_4px_12px_rgba(139,92,246,0.3)]' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
            >
              Chat
            </button>
            <button 
              onClick={() => setView('upload')}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                view === 'upload' ? 'bg-primary-600 text-white shadow-[0_4px_12px_rgba(139,92,246,0.3)]' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
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
