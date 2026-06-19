import { MessageSquare, Plus, Network, Settings, LogOut } from 'lucide-react';

export default function Sidebar({ onLogout, onNewChat, sessions, currentSessionId, onSelectSession }) {
  return (
    <div className="w-72 bg-dark-900 border-r border-white/5 flex flex-col h-screen">
      <div className="p-6 border-b border-white/5">
        <div className="flex items-center gap-3 text-white font-display font-bold text-xl mb-6">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center flex-shrink-0 shadow-[0_0_15px_rgba(20,184,166,0.3)]">
            <Network size={18} className="text-white" />
          </div>
          Nexus AI
        </div>
        
        <button 
          onClick={onNewChat}
          className="w-full flex items-center gap-2 bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-xl px-4 py-3 transition-all duration-300 text-sm font-medium shadow-sm hover:shadow-md"
        >
          <Plus size={18} />
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-1 scrollbar-hide">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 px-3 mt-2">
          Recent Sessions
        </div>
        
        {sessions.map(session => (
          <button
            key={session.id}
            onClick={() => onSelectSession(session.id)}
            className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl text-left transition-all duration-300 group ${
              currentSessionId === session.id 
                ? 'bg-primary-500/10 text-primary-400 border border-primary-500/20 shadow-inner' 
                : 'text-slate-400 hover:bg-white/5 hover:text-slate-200 hover:translate-x-1 border border-transparent'
            }`}
          >
            <MessageSquare size={18} className={currentSessionId === session.id ? 'text-primary-400' : 'text-slate-500 group-hover:text-slate-300 transition-colors'} />
            <span className="truncate text-sm font-medium">{session.name}</span>
          </button>
        ))}
        
        {sessions.length === 0 && (
          <div className="text-center px-4 py-8 text-slate-500 text-sm">
            No chat history yet. Start a new conversation!
          </div>
        )}
      </div>

      <div className="p-4 border-t border-white/5">
        <button 
          onClick={onLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all duration-300 text-sm font-medium"
        >
          <LogOut size={18} />
          Log Out
        </button>
      </div>
    </div>
  );
}
