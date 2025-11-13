import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { FileText, Sparkles, BookOpen, Lightbulb, Brain, MessageSquare, ChevronLeft, ChevronRight, Target, Clock, BarChart3 } from "lucide-react";
import { toast } from 'react-toastify';
import { PulseLoader } from 'react-spinners';
import api from "../api/backend";
import Loader from "../components/Loader";
import NoContentMessage from "../components/NoContentMessage";
import { hasExtractedContent, getExtractedConcepts } from "../utils/contentCheck";

export default function Notes() {
  const location = useLocation();
  const topicFromHome = location.state?.topic;
  
  const [topic, setTopic] = useState(topicFromHome || "");
  const [notes, setNotes] = useState(null);
  const [loading, setLoading] = useState(false);
  const [flashcardIndex, setFlashcardIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [suggestedTopics, setSuggestedTopics] = useState([]);

  // Check if content exists
  if (!hasExtractedContent()) {
    return <NoContentMessage feature="the Notes feature" />;
  }

  useEffect(() => {
    // Load suggested topics
    const concepts = getExtractedConcepts();
    setSuggestedTopics(concepts);

    // If coming from home with a topic, generate notes immediately
    if (topicFromHome) {
      generateNotes(topicFromHome);
    }
  }, [topicFromHome]);

  const generateNotes = async (topicText = topic) => {
    const finalTopic = topicText || topic;
    if (!finalTopic.trim()) {
      toast.warning("Please enter a topic or select from suggestions");
      return;
    }

    setLoading(true);
    setNotes(null);
    try {
      console.log("Generating notes for topic:", finalTopic);
      const res = await api.post("/notes/generate", {
        topic: finalTopic,
        use_stored_content: true
      });
      console.log("Notes generated successfully:", res.data);
      setNotes(res.data.notes);
      setFlashcardIndex(0);
      setShowAnswer(false);
      setTopic(finalTopic);
      toast.success("Notes generated successfully!");
    } catch (err) {
      console.error("Notes generation error:", err);
      console.error("Error response:", err.response?.data);
      
      // More helpful error message
      const errorDetail = err.response?.data?.detail || err.message;
      
      // Check if it's a rate limit error
      if (errorDetail && (errorDetail.includes("429") || errorDetail.includes("quota") || errorDetail.includes("rate limit"))) {
        toast.error(
          "API Rate Limit Reached! You've hit the daily quota (50 requests/day). Please wait a few moments or try again tomorrow.",
          { autoClose: 8000 }
        );
      } else {
        toast.error(
          `Failed to generate notes: ${errorDetail}`,
          { autoClose: 5000 }
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (concept) => {
    const conceptText = typeof concept === 'string' ? concept : concept.title || concept.name || concept;
    setTopic(conceptText);
    generateNotes(conceptText);
  };

  const nextFlashcard = () => {
    if (notes && notes.flashcards) {
      setFlashcardIndex((flashcardIndex + 1) % notes.flashcards.length);
      setShowAnswer(false);
    }
  };

  const prevFlashcard = () => {
    if (notes && notes.flashcards) {
      setFlashcardIndex((flashcardIndex - 1 + notes.flashcards.length) % notes.flashcards.length);
      setShowAnswer(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 p-4 sm:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-600 to-red-600 flex items-center justify-center">
              <FileText className="w-5 h-5 text-white" strokeWidth={2} />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-white">
                AI Study Notes
              </h1>
              <p className="text-sm text-slate-400">
                Automated notes, flashcards, mind maps, and practice questions
              </p>
            </div>
          </div>
        </div>

        {/* Suggested Topics */}
        {suggestedTopics.length > 0 && !notes && (
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 mb-6">
            <h3 className="text-base font-medium text-white mb-4 flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-yellow-400" strokeWidth={2} />
              <span>Suggested Topics</span>
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
              {suggestedTopics.map((item, i) => {
                const conceptText = typeof item === 'string' ? item : item.title || item.name || item;
                return (
                  <button
                    key={i}
                    onClick={() => handleSuggestionClick(item)}
                    className="bg-slate-800/50 hover:bg-slate-800 border border-slate-700 hover:border-orange-500/50 rounded-lg p-3 text-sm text-slate-300 hover:text-white transition-all text-left"
                  >
                    <Target className="w-4 h-4 inline-block mr-2 text-orange-400" strokeWidth={2} />
                    {conceptText}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Input Section */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 mb-6">
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && generateNotes()}
              placeholder="Enter topic (e.g., Event Loop, Async Programming...)"
              className="flex-1 bg-slate-900 text-white border border-slate-700 px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent placeholder-slate-500 text-sm transition-all"
              disabled={loading}
            />
            <button
              onClick={() => generateNotes()}
              disabled={loading}
              className="bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-500 hover:to-red-500 text-white font-medium px-6 py-3 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 justify-center"
            >
              {loading ? (
                <>
                  <PulseLoader color="#ffffff" size={8} />
                  <span>Generating...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" strokeWidth={2} />
                  Generate Notes
                </>
              )}
            </button>
          </div>
        </div>

        {loading && (
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-12 text-center">
            <Loader />
            <p className="text-slate-300 mt-4 text-sm">Generating comprehensive study notes with AI...</p>
            <p className="text-slate-500 text-xs mt-2">This may take a moment</p>
          </div>
        )}

        {notes && !loading && (
          <div className="space-y-4">
            {/* Back Button */}
            <button
              onClick={() => {
                setNotes(null);
                setTopic("");
              }}
              className="bg-slate-900/50 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white px-4 py-2 rounded-lg transition-all flex items-center gap-2 text-sm"
            >
              <ChevronLeft className="w-4 h-4" strokeWidth={2} />
              Generate Different Notes
            </button>

            {/* Summary */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
                <h2 className="text-lg font-semibold text-white flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-orange-600/20 flex items-center justify-center border border-orange-500/30">
                    <BookOpen className="w-5 h-5 text-orange-400" strokeWidth={2} />
                  </div>
                  Summary
                </h2>
                <div className="flex gap-2 text-xs">
                  <span className="bg-orange-500/10 text-orange-400 border border-orange-500/20 px-3 py-1.5 rounded-lg flex items-center gap-1.5 font-medium">
                    <Clock className="w-3.5 h-3.5" strokeWidth={2} />
                    {notes.estimated_study_time} min
                  </span>
                  <span className="bg-red-500/10 text-red-400 border border-red-500/20 px-3 py-1.5 rounded-lg flex items-center gap-1.5 font-medium">
                    <BarChart3 className="w-3.5 h-3.5" strokeWidth={2} />
                    {notes.difficulty_level}
                  </span>
                </div>
              </div>
              <div className="text-slate-300 whitespace-pre-wrap text-sm leading-relaxed">
                {notes.summary}
              </div>
            </div>

            {/* Key Points */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-orange-600/20 flex items-center justify-center border border-orange-500/30">
                  <Target className="w-5 h-5 text-orange-400" strokeWidth={2} />
                </div>
                Key Points
              </h2>
              <ul className="space-y-2">
                {notes.key_points && notes.key_points.map((point, i) => {
                  // Handle both string and object formats
                  const pointText = typeof point === 'string' 
                    ? point 
                    : point.point || point.text || point.title || JSON.stringify(point);
                  
                  return (
                    <li key={i} className="flex items-start gap-3 bg-slate-800/30 border border-slate-800 rounded-lg p-3 hover:border-slate-700 transition-all">
                      <span className="flex-shrink-0 w-6 h-6 rounded-md bg-gradient-to-br from-orange-600 to-red-600 flex items-center justify-center text-white font-medium text-xs">
                        {i + 1}
                      </span>
                      <span className="text-slate-300 text-sm flex-1">{pointText}</span>
                    </li>
                  );
                })}
              </ul>
            </div>

            {/* Definitions */}
            {notes.definitions && (
              <div className="glass-effect rounded-2xl p-6 shadow-xl">
                <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                  <BookOpen className="w-6 h-6 text-blue-400" />
                  Definitions
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Array.isArray(notes.definitions) ? (
                    // Handle array of definition objects
                    notes.definitions.map((item, i) => {
                      const term = item.term || item.word || item.concept || `Term ${i + 1}`;
                      const definition = item.definition || item.def || item.meaning || JSON.stringify(item);
                      return (
                        <div key={i} className="glass-effect rounded-xl p-4 border border-blue-500/20 hover:border-blue-500/50 transition-all">
                          <h3 className="font-bold text-blue-300 mb-2">{term}</h3>
                          <p className="text-gray-300 text-sm leading-relaxed">{definition}</p>
                        </div>
                      );
                    })
                  ) : (
                    // Handle object of key-value pairs
                    Object.entries(notes.definitions).map(([term, def], i) => (
                      <div key={i} className="glass-effect rounded-xl p-4 border border-blue-500/20 hover:border-blue-500/50 transition-all">
                        <h3 className="font-bold text-blue-300 mb-2">{term}</h3>
                        <p className="text-gray-300 text-sm leading-relaxed">{typeof def === 'string' ? def : JSON.stringify(def)}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* Flashcards */}
            {notes.flashcards && notes.flashcards.length > 0 && (
              <div className="glass-effect rounded-2xl p-6 shadow-xl">
                <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                  <MessageSquare className="w-6 h-6 text-purple-400" />
                  Flashcards
                </h2>
                <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-purple-900/50 to-indigo-900/50 p-8 min-h-[320px] flex flex-col items-center justify-between border border-purple-500/30">
                  <div className="text-center mb-6 w-full">
                    <div className="glass-effect inline-block px-4 py-2 rounded-lg text-sm text-purple-300 mb-6">
                      Card {flashcardIndex + 1} of {notes.flashcards.length}
                    </div>
                    <div className="glass-effect rounded-2xl p-8 min-h-[180px] flex items-center justify-center border border-white/10">
                      {!showAnswer ? (
                        <div className="text-center">
                          <p className="text-gray-400 text-sm mb-3 font-medium">Question:</p>
                          <p className="text-white text-xl font-medium leading-relaxed">
                            {notes.flashcards[flashcardIndex].question}
                          </p>
                        </div>
                      ) : (
                        <div className="text-center">
                          <p className="text-gray-400 text-sm mb-3 font-medium">Answer:</p>
                          <p className="text-teal-300 text-xl font-medium leading-relaxed">
                            {notes.flashcards[flashcardIndex].answer}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={prevFlashcard}
                      className="glass-effect hover:bg-white/10 text-white px-5 py-3 rounded-xl transition-all flex items-center gap-2 font-medium"
                    >
                      <ChevronLeft className="w-4 h-4" />
                      Previous
                    </button>
                    <button
                      onClick={() => setShowAnswer(!showAnswer)}
                      className="bg-gradient-to-r from-teal-600 to-cyan-600 hover:shadow-lg hover:shadow-teal-500/50 text-white px-6 py-3 rounded-xl transition-all font-semibold"
                    >
                      {showAnswer ? "Show Question" : "Show Answer"}
                    </button>
                    <button
                      onClick={nextFlashcard}
                      className="glass-effect hover:bg-white/10 text-white px-5 py-3 rounded-xl transition-all flex items-center gap-2 font-medium"
                    >
                      Next
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Mind Map */}
            {notes.mind_map && (
              <div className="glass-effect rounded-2xl p-6 shadow-xl">
                <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                  <Brain className="w-6 h-6 text-cyan-400" />
                  Mind Map Structure
                </h2>
                <div className="flex flex-col items-center">
                  <div className="bg-gradient-to-r from-teal-600 to-cyan-600 text-white px-8 py-4 rounded-2xl font-bold text-lg mb-8 shadow-lg">
                    {notes.mind_map.central_topic}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 w-full">
                    {notes.mind_map.branches && notes.mind_map.branches.map((branch, i) => (
                      <div 
                        key={i} 
                        className="glass-effect rounded-xl p-5 border border-cyan-500/30 hover:border-cyan-500/60 transition-all hover:transform hover:-translate-y-1"
                      >
                        <h3 className="font-bold text-cyan-300 mb-2 text-lg">{branch.title}</h3>
                        <p className="text-gray-300 text-sm leading-relaxed">{branch.details}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Practice Questions */}
            {notes.practice_questions && notes.practice_questions.length > 0 && (
              <div className="glass-effect rounded-2xl p-6 shadow-xl">
                <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                  <Lightbulb className="w-6 h-6 text-yellow-400" />
                  Practice Questions
                </h2>
                <div className="space-y-4">
                  {notes.practice_questions.map((q, i) => (
                    <div key={i} className="glass-effect rounded-xl p-5 border border-yellow-500/20 hover:border-yellow-500/40 transition-all">
                      <div className="flex items-center justify-between mb-3">
                        <span className="flex items-center gap-2">
                          <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-yellow-600 to-orange-600 flex items-center justify-center text-white font-bold text-sm">
                            Q{i + 1}
                          </span>
                        </span>
                        <span className="glass-effect px-3 py-1 rounded-lg text-xs text-gray-300 font-medium">
                          {q.difficulty || 'medium'}
                        </span>
                      </div>
                      <p className="text-white mb-3 text-lg">{q.question}</p>
                      {q.hint && (
                        <div className="glass-effect rounded-lg p-3 mt-3 border border-blue-500/20">
                          <p className="text-sm text-blue-300 flex items-center gap-2">
                            <Lightbulb className="w-4 h-4" />
                            <span className="font-medium">Hint:</span>
                            <span className="text-gray-300">{q.hint}</span>
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
