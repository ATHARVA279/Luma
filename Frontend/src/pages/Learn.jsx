import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { BookOpen, Send, Lightbulb, BookmarkCheck, Sparkles, Target } from "lucide-react";
import { toast } from 'react-toastify';
import { BeatLoader } from 'react-spinners';
import api from "../api/backend";
import Loader from "../components/Loader";
import NoContentMessage from "../components/NoContentMessage";
import { hasExtractedContent, getExtractedConcepts } from "../utils/contentCheck";

export default function Learn() {
  const location = useLocation();
  const conceptFromHome = location.state?.concept;
  
  const [concept, setConcept] = useState(conceptFromHome || "");
  const [explanation, setExplanation] = useState("");
  const [loading, setLoading] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [askingQuestion, setAskingQuestion] = useState(false);
  const [savedExplanations, setSavedExplanations] = useState({});
  const [suggestedConcepts, setSuggestedConcepts] = useState([]);

  // Check if content exists
  if (!hasExtractedContent()) {
    return <NoContentMessage feature="the Learn feature" />;
  }

  useEffect(() => {
    // Load saved explanations from localStorage
    const saved = localStorage.getItem("learnExplanations");
    let parsed = {};
    if (saved) {
      parsed = JSON.parse(saved);
      setSavedExplanations(parsed);
    }

    // Load suggested concepts
    const concepts = getExtractedConcepts();
    setSuggestedConcepts(concepts);

    // If coming from home with a concept, fetch it
    if (conceptFromHome) {
      const conceptKey = typeof conceptFromHome === 'string' ? conceptFromHome : conceptFromHome.title || conceptFromHome.name;
      // Check if we have saved explanation
      if (saved && parsed[conceptKey]) {
        setExplanation(parsed[conceptKey]);
      } else {
        // Only fetch if not already loaded
        if (!explanation) {
          fetchConceptDetail(conceptFromHome);
        }
      }
    }
  }, []); // Remove conceptFromHome from dependencies to prevent re-fetching

  const fetchConceptDetail = async (conceptText) => {
    setLoading(true);
    setExplanation("");
    try {
      const res = await api.post("/concept-detail", { concept: conceptText });
      const newExplanation = res.data.explanation;
      setExplanation(newExplanation);
      
      // Save to localStorage
      const conceptKey = typeof conceptText === 'string' ? conceptText : conceptText.title || conceptText.name || conceptText;
      const updated = { ...savedExplanations, [conceptKey]: newExplanation };
      setSavedExplanations(updated);
      localStorage.setItem("learnExplanations", JSON.stringify(updated));
      toast.success("Concept loaded successfully!");
    } catch (err) {
      console.error(err);
      toast.error("Failed to load explanation. Please try again.");
      setExplanation("Failed to load explanation. Please make sure you've extracted content first.");
    } finally {
      setLoading(false);
    }
  };

  const handleLearnConcept = () => {
    if (!concept.trim()) {
      toast.warning("Please enter a concept to learn about");
      return;
    }
    
    // Check if we have saved explanation
    if (savedExplanations[concept]) {
      setExplanation(savedExplanations[concept]);
    } else {
      fetchConceptDetail(concept);
    }
  };

  const handleConceptClick = (conceptItem) => {
    const conceptText = typeof conceptItem === 'string' ? conceptItem : conceptItem.title || conceptItem.name || conceptItem;
    setConcept(conceptText);
    
    // Check if we have saved explanation
    if (savedExplanations[conceptText]) {
      setExplanation(savedExplanations[conceptText]);
    } else {
      fetchConceptDetail(conceptText);
    }
  };

  const handleAskQuestion = async () => {
    if (!question.trim()) {
      toast.warning("Please enter a question");
      return;
    }

    setAskingQuestion(true);
    setAnswer("");
    try {
      const res = await api.post("/chat", { 
        question: `About ${concept}: ${question}`,
        history: []
      });
      setAnswer(res.data.answer);
      toast.success("Answer generated!");
    } catch (err) {
      console.error(err);
      toast.error("Failed to get answer. Please try again.");
      setAnswer("Failed to get answer. Please try again.");
    } finally {
      setAskingQuestion(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 p-8 mb-8 shadow-2xl">
          <div className="absolute inset-0 bg-black/10"></div>
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-12 h-12 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center text-3xl">
                <span>💡</span>
              </div>
              <h1 className="text-4xl font-bold text-white tracking-tight">Learn Concepts</h1>
            </div>
            <p className="text-xl text-white/90 font-medium">
              Deep dive into any topic with AI-powered explanations
            </p>
          </div>
        </div>

        {/* Suggested Concepts */}
        {suggestedConcepts.length > 0 && !explanation && (
          <div className="glass-effect rounded-2xl p-6 mb-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-yellow-400" />
              <span>Suggested Topics from Your Content</span>
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {suggestedConcepts.map((item, i) => {
                const conceptText = typeof item === 'string' ? item : item.title || item.name || item;
                return (
                  <button
                    key={i}
                    onClick={() => handleConceptClick(item)}
                    className="glass-effect hover:bg-white/10 p-3 rounded-xl text-left transition-all group border border-white/10 hover:border-violet-500/50"
                  >
                    <div className="text-sm font-medium text-white group-hover:text-violet-300 transition-colors line-clamp-2">
                      {conceptText}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}
        
        {/* Concept Input */}
        <div className="glass-effect rounded-2xl p-6 mb-6">
          <label className="block text-sm font-medium text-gray-300 mb-3">
            What would you like to learn about?
          </label>
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              placeholder="e.g., Machine Learning, Photosynthesis, React Hooks..."
              value={concept}
              onChange={(e) => setConcept(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleLearnConcept()}
              className="flex-1 bg-gray-800/50 text-white border border-gray-700 px-5 py-4 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-500 transition-all"
            />
            <button
              onClick={handleLearnConcept}
              disabled={loading}
              className="gradient-primary hover:shadow-lg hover:shadow-blue-500/50 text-white px-8 py-4 rounded-xl font-semibold disabled:opacity-50 transition-all transform hover:scale-105"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <BeatLoader color="#ffffff" size={8} />
                  Learning...
                </span>
              ) : "Learn"}
            </button>
          </div>
        </div>

        {loading && (
          <div className="glass-effect rounded-2xl p-12 text-center">
            <BeatLoader color="#8b5cf6" size={15} />
            <p className="text-gray-400 mt-4">Generating explanation with AI...</p>
          </div>
        )}

        {/* Explanation */}
        {explanation && !loading && (
          <div className="space-y-6">
            <div className="glass-effect rounded-2xl p-6 border border-blue-500/30">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                  <span>📖</span>
                  <span>Explanation</span>
                </h3>
                <span className="text-xs px-3 py-1 bg-blue-600/30 text-blue-300 rounded-full">
                  Saved
                </span>
              </div>
              <div className="text-gray-300 whitespace-pre-wrap leading-relaxed">
                {explanation}
              </div>
              <p className="text-xs text-gray-500 mt-4 flex items-center gap-2">
                <span>⚡</span>
                <span>Powered by Advanced RAG with Hybrid Search</span>
              </p>
            </div>

            {/* Q&A Section */}
            <div className="glass-effect rounded-2xl p-6">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <span>❓</span>
                <span>Ask Follow-up Questions</span>
              </h3>
              <div className="flex flex-col sm:flex-row gap-3 mb-4">
                <input
                  type="text"
                  placeholder="Ask anything about this concept..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAskQuestion()}
                  className="flex-1 bg-gray-800/50 text-white border border-gray-700 px-5 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 placeholder-gray-500"
                />
                <button
                  onClick={handleAskQuestion}
                  disabled={askingQuestion}
                  className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:shadow-lg hover:shadow-emerald-500/50 text-white px-8 py-3 rounded-xl font-semibold disabled:opacity-50 transition-all"
                >
                  {askingQuestion ? "Thinking..." : "Ask"}
                </button>
              </div>

              {answer && (
                <div className="glass-effect border border-emerald-500/30 rounded-xl p-5 bg-emerald-900/10">
                  <p className="text-sm font-semibold text-emerald-400 mb-2 flex items-center gap-2">
                    <span>💬</span>
                    <span>Answer:</span>
                  </p>
                  <p className="text-gray-300 leading-relaxed">{answer}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
