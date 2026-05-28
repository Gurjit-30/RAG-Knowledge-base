import { MessageSquare, Plus, FileText, Settings, LogOut } from 'lucide-react';

export default function Sidebar({ onLogout, onNewChat, sessions, currentSessionId, onSelectSession }) {
  return (
    <div className="w-72 bg-dark-900 border-r border-dark-700 flex flex-col h-screen">
      <div className="p-4 border-b border-dark-700">
        <div className="flex items-center gap-3 text-primary-500 font-bold text-xl mb-4">
          <div className="w-8 h-8 rounded-lg bg-primary-500/20 flex items-center justify-center">
            <FileText size={20} className="text-primary-400" />
          </div>
          RAG Base
        </div>
        
        <button 
          onClick={onNewChat}
          className="w-full flex items-center gap-2 bg-dark-800 hover:bg-dark-700 text-slate-200 border border-dark-600 rounded-xl px-4 py-3 transition-colors text-sm font-medium"
        >
          <Plus size={18} />
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-hide">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 px-2">
          Recent Sessions
        </div>
        
        {sessions.map(session => (
          <button
            key={session.id}
            onClick={() => onSelectSession(session.id)}
            className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl text-left transition-colors ${
              currentSessionId === session.id 
                ? 'bg-primary-500/10 text-primary-400 border border-primary-500/20' 
                : 'text-slate-400 hover:bg-dark-800 hover:text-slate-200'
            }`}
          >
            <MessageSquare size={18} />
            <span className="truncate text-sm font-medium">{session.name}</span>
          </button>
        ))}
        
        {sessions.length === 0 && (
          <div className="text-center px-4 py-8 text-slate-500 text-sm">
            No chat history yet. Start a new conversation!
          </div>
        )}
      </div>

      <div className="p-4 border-t border-dark-700">
        <button 
          onClick={onLogout}
          className="w-full flex items-center gap-3 px-3 py-2 text-slate-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors text-sm"
        >
          <LogOut size={18} />
          Log Out
        </button>
      </div>
    </div>
  );
}
