import { useState, useEffect, useRef } from "react";
import { MessageCircle, Send, Trash2, Settings } from "lucide-react";
import { toast } from 'react-toastify';
import { PulseLoader } from 'react-spinners';
import api from "../api/backend";
import Loader from "../components/Loader";
import NoContentMessage from "../components/NoContentMessage";
import { hasExtractedContent } from "../utils/contentCheck";

export default function Chat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [searchMethod, setSearchMethod] = useState("hybrid");
  const messagesEndRef = useRef(null);

  // Check if content exists
  if (!hasExtractedContent()) {
    return <NoContentMessage feature="the Chat feature" />;
  }

  useEffect(() => {
    const savedSessionId = localStorage.getItem("chatSessionId") || `user_${Date.now()}`;
    localStorage.setItem("chatSessionId", savedSessionId);
    setSessionId(savedSessionId);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: "user", text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.post("/chat/advanced", { 
        question: input,
        session_id: sessionId,
        search_method: searchMethod,
        use_memory: true,
        top_k: 4
      });
      
      const aiMessage = { 
        role: "ai", 
        text: res.data.answer,
        sources: res.data.sources_used,
        searchScores: res.data.search_scores,
        enhanced: res.data.query_enhanced
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      console.error(err);
      toast.error("Failed to get response. Make sure you've extracted content first.");
      const errorMessage = { 
        role: "ai", 
        text: "Sorry, I couldn't process that. Make sure you've extracted content first." 
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    api.delete(`/chat/session/${sessionId}`).catch(console.error);
    toast.success("Chat cleared!");
  };

  const getSearchMethodInfo = () => {
    const info = {
      hybrid: { name: "Balanced", desc: "Best for most questions" },
      rrf: { name: "Most Accurate", desc: "Combines multiple methods" },
      tfidf: { name: "Keyword Match", desc: "Fast keyword-based search" },
      bm25: { name: "Context Search", desc: "Understands context better" }
    };
    return info[searchMethod] || info.hybrid;
  };

  return (
    <div className="min-h-screen bg-slate-950 p-4 sm:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
        {/* Header */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 mb-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-600 to-red-600 flex items-center justify-center">
                <MessageCircle className="w-5 h-5 text-white" strokeWidth={2} />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">AI Chat Assistant</h2>
                <p className="text-sm text-slate-400">Ask questions about your extracted content</p>
              </div>
            </div>
            <div className="flex gap-3 items-center">
              <select 
                value={searchMethod}
                onChange={(e) => setSearchMethod(e.target.value)}
                className="bg-slate-900 text-white px-3 py-2 rounded-lg border border-slate-700 focus:outline-none focus:ring-2 focus:ring-orange-500 text-sm"
              >
                <option value="hybrid">Balanced</option>
                <option value="rrf">Most Accurate</option>
                <option value="tfidf">Keyword Match</option>
                <option value="bm25">Context Search</option>
              </select>
              <button 
                onClick={clearChat}
                className="bg-red-600/10 hover:bg-red-600/20 border border-red-500/30 text-red-400 hover:text-red-300 px-3 py-2 rounded-lg transition-all flex items-center gap-2"
                title="Clear conversation history"
              >
                <Trash2 className="w-4 h-4" strokeWidth={2} />
                <span className="hidden sm:inline text-sm">Clear</span>
              </button>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 bg-slate-900/50 border border-slate-800 rounded-xl p-6 overflow-y-auto mb-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-slate-400 mt-12">
              <div className="w-16 h-16 mx-auto mb-4 rounded-lg bg-orange-600/20 flex items-center justify-center border border-orange-500/30">
                <MessageCircle className="w-8 h-8 text-orange-400" strokeWidth={2} />
              </div>
              <p className="text-base mb-2">Hi! I'm your AI learning assistant.</p>
              <p className="text-sm">Ask me anything about the content you've extracted!</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[75%] rounded-lg p-4 ${
                msg.role === "user" 
                  ? "bg-gradient-to-br from-orange-600 to-red-600 text-white" 
                  : "bg-slate-800/50 border border-slate-700 text-slate-100"
              }`}>
                <p className="whitespace-pre-wrap text-sm">{msg.text}</p>
                {msg.enhanced && (
                  <p className="text-xs mt-2 opacity-75">
                    Enhanced with conversation context
                  </p>
                )}
                {msg.sources > 0 && (
                  <p className="text-xs mt-2 opacity-75">
                    Found in {msg.sources} source{msg.sources > 1 ? 's' : ''}
                  </p>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                <PulseLoader color="#f97316" size={8} />
                <p className="text-slate-400 text-xs mt-2">Thinking...</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              placeholder="Ask a question about your content..."
              className="flex-1 bg-slate-900 text-white border border-slate-700 px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 placeholder-slate-500 text-sm"
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-500 hover:to-red-500 text-white px-6 py-3 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
            >
              <Send className="w-4 h-4" strokeWidth={2} />
              <span className="hidden sm:inline">Send</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
