import { useState, useEffect, useRef } from "react";
import { toast } from 'react-toastify';
import { BarLoader } from 'react-spinners';
import api from "../api/backend";
import Loader from "../components/Loader";

export default function Chat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [searchMethod, setSearchMethod] = useState("hybrid");
  const messagesEndRef = useRef(null);

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
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="max-w-5xl mx-auto flex flex-col h-[calc(100vh-100px)]">
        <div className="bg-gradient-to-r from-purple-900 to-indigo-900 rounded-lg shadow-xl p-6 mb-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">🤖 AI Chat Assistant</h2>
              <p className="text-purple-200">Ask questions about your extracted content</p>
            </div>
            <div className="flex gap-3 items-end">
              <div className="flex flex-col">
                <label className="text-xs text-purple-300 mb-1">Search Quality:</label>
                <select 
                  value={searchMethod}
                  onChange={(e) => setSearchMethod(e.target.value)}
                  className="bg-purple-800 text-white px-4 py-2 rounded-lg border border-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-400 text-sm"
                  title={getSearchMethodInfo().desc}
                >
                  <option value="hybrid">⚡ Balanced (Recommended)</option>
                  <option value="rrf">🎯 Most Accurate</option>
                  <option value="tfidf">📊 Keyword Match</option>
                  <option value="bm25">🔍 Context Search</option>
                </select>
                <span className="text-xs text-purple-300 mt-1">{getSearchMethodInfo().desc}</span>
              </div>
              <button 
                onClick={clearChat}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
                title="Clear conversation history"
              >
                Clear Chat
              </button>
            </div>
          </div>
          <p className="text-xs text-purple-300 mt-3">
            💡 I remember our conversation | 🧠 Just ask follow-up questions naturally
          </p>
        </div>

        <div className="flex-1 bg-gray-800 rounded-lg shadow-xl p-6 overflow-y-auto mb-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-400 mt-12">
              <p className="text-lg mb-2">👋 Hi! I'm your AI learning assistant.</p>
              <p className="text-sm">Ask me anything about the content you've extracted!</p>
              <p className="text-xs mt-4 text-gray-500">
                Tip: I remember our conversation, so you can ask follow-up questions
              </p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[75%] rounded-lg p-4 ${
                msg.role === "user" 
                  ? "bg-indigo-600 text-white" 
                  : "bg-gray-700 text-gray-100"
              }`}>
                <p className="whitespace-pre-wrap">{msg.text}</p>
                {msg.enhanced && (
                  <p className="text-xs mt-2 opacity-75">
                    💭 Enhanced with conversation context
                  </p>
                )}
                {msg.sources > 0 && (
                  <p className="text-xs mt-2 opacity-75">
                    📚 Found in {msg.sources} source{msg.sources > 1 ? 's' : ''}
                  </p>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-700 rounded-lg p-4 min-w-[80px]">
                <BarLoader color="#8b5cf6" width="60px" />
                <p className="text-gray-400 text-xs mt-2">Thinking...</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="bg-gray-800 rounded-lg shadow-xl p-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              placeholder="Ask a question about your content..."
              className="flex-1 bg-gray-700 text-white border border-gray-600 px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-400"
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="bg-purple-600 hover:bg-purple-700 text-white px-8 py-3 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
