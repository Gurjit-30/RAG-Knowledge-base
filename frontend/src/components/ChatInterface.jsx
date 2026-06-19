import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { ArrowUp, User, Sparkles, Loader2, FileText, ChevronRight } from 'lucide-react';

export default function ChatInterface({ token, sessionId }) {
  const [messages, setMessages] = useState([
    { role: 'ai', content: 'Welcome to Nexus AI. I have access to your uploaded knowledge base. How can I assist you today?' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsTyping(true);

    try {
      // Setup the fetch request to our streaming endpoint
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/ask/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ query: userMsg, session_id: sessionId })
      });

      if (!response.ok) {
        throw new Error(response.statusText);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      // Add empty AI message to stream into
      setMessages(prev => [...prev, { role: 'ai', content: '', sources: [] }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter(Boolean);

        for (const line of lines) {
          try {
            const data = JSON.parse(line);
            
            if (data.type === 'token') {
              setMessages(prev => {
                const newMsgs = [...prev];
                const lastMsg = newMsgs[newMsgs.length - 1];
                lastMsg.content += data.data;
                return newMsgs;
              });
            } else if (data.type === 'sources') {
              setMessages(prev => {
                const newMsgs = [...prev];
                const lastMsg = newMsgs[newMsgs.length - 1];
                lastMsg.sources = data.data;
                return newMsgs;
              });
            } else if (data.type === 'error') {
              setMessages(prev => {
                const newMsgs = [...prev];
                const lastMsg = newMsgs[newMsgs.length - 1];
                lastMsg.content += `\n\n**Error:** ${data.data}`;
                return newMsgs;
              });
            }
          } catch (err) {
            console.error('Failed to parse stream JSON', err);
          }
        }
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', content: 'Sorry, I encountered an error communicating with the server.' }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-dark-900">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-hide">
        {messages.map((msg, i) => (
          <div 
            key={i} 
            className={`flex gap-4 max-w-4xl mx-auto ${msg.role === 'user' ? 'flex-row-reverse' : ''} animate-fade-in-up`}
          >
            <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
              msg.role === 'user' ? 'bg-primary-600' : 'bg-dark-700'
            }`}>
              {msg.role === 'user' ? <User size={20} className="text-white" /> : <Sparkles size={20} className="text-primary-400" />}
            </div>
            
            <div className={`max-w-[80%] p-5 ${
              msg.role === 'user' 
                ? 'bg-primary-600 text-white rounded-3xl rounded-tr-sm shadow-md' 
                : 'glass-panel rounded-2xl rounded-tl-sm'
            }`}>
              <div className="prose prose-invert max-w-none text-sm md:text-base leading-relaxed">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
              
              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-4 pt-4 border-t border-dark-600/50">
                  <p className="text-xs text-slate-400 mb-2 font-medium">Sources:</p>
                  <div className="flex flex-wrap gap-2">
                    {msg.sources.map((s, idx) => (
                      <span key={idx} className="inline-flex items-center px-2.5 py-1 rounded-md bg-dark-800 border border-dark-600 text-xs text-slate-300">
                        {s.filename} (Page {s.page_number})
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Empty State Suggestions */}
        {messages.length === 1 && messages[0].role === 'ai' && (
          <div className="max-w-3xl mx-auto pt-8 pb-4 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-8">
              {[
                "Summarize the key findings from the latest document",
                "Extract the most actionable insights",
                "Explain the methodology used in the reports",
                "What are the main limitations mentioned?"
              ].map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(suggestion)}
                  className="flex items-start gap-3 p-4 text-left rounded-xl bg-dark-800/40 border border-white/5 hover:border-primary-500/30 hover:bg-white/5 transition-all duration-300 group shadow-sm"
                >
                  <div className="mt-0.5 bg-dark-700/50 p-1.5 rounded-lg group-hover:bg-primary-500/20 group-hover:text-primary-400 transition-colors">
                    <FileText size={16} />
                  </div>
                  <span className="text-sm text-slate-300 group-hover:text-slate-200">{suggestion}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-dark-900 border-t border-dark-700/50">
        <div className="max-w-4xl mx-auto relative">
          <form onSubmit={handleSend} className="relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your documents..."
              className="w-full bg-dark-800/80 border border-white/10 text-white placeholder-slate-400 rounded-full py-4 pl-6 pr-16 focus:outline-none focus:ring-2 focus:ring-primary-500/50 shadow-lg transition-all"
              disabled={isTyping}
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-11 h-11 rounded-full bg-white text-dark-900 hover:bg-slate-200 flex items-center justify-center transition-all disabled:opacity-50 disabled:bg-dark-700 disabled:text-slate-500 shadow-[0_0_15px_rgba(255,255,255,0.1)]"
            >
              {isTyping ? <Loader2 size={20} className="animate-spin" /> : <ArrowUp size={20} className="stroke-[2.5]" />}
            </button>
          </form>
          <div className="text-center mt-2 text-xs text-slate-500">
            AI can make mistakes. Consider verifying important information.
          </div>
        </div>
      </div>
    </div>
  );
}
