import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { FileText, BookOpen, Lightbulb, Brain, MessageSquare, ChevronLeft, ChevronRight, Target, Clock, BarChart3, Sparkles } from "lucide-react";
import { toast } from 'react-toastify';
import { PulseLoader } from 'react-spinners';
import api from "../api/backend";
import Loader from "../components/Loader";
import NoContentMessage from "../components/NoContentMessage";
import { hasExtractedContent, getExtractedConcepts } from "../utils/contentCheck";
import PageLayout from "../components/layout/PageLayout";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Card from "../components/ui/Card";
import Badge from "../components/ui/Badge";

export default function Notes() {
  const location = useLocation();
  const topicFromHome = location.state?.topic;

  const [topic, setTopic] = useState(topicFromHome || "");
  const [notes, setNotes] = useState(null);
  const [loading, setLoading] = useState(false);
  const [flashcardIndex, setFlashcardIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [suggestedTopics, setSuggestedTopics] = useState([]);

  if (!hasExtractedContent()) {
    return (
      <PageLayout>
        <NoContentMessage feature="the Notes feature" />
      </PageLayout>
    );
  }

  useEffect(() => {
    const concepts = getExtractedConcepts();
    setSuggestedTopics(concepts);

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

    const documentId = localStorage.getItem("extractedDocumentId");
    if (!documentId) {
      toast.error("No document selected. Please extract content first.");
      return;
    }

    setLoading(true);
    setNotes(null);
    try {
      const res = await api.post("/notes/generate", {
        topic: finalTopic,
        use_stored_content: true,
        document_id: documentId
      });
      setNotes(res.data.notes);
      setFlashcardIndex(0);
      setShowAnswer(false);
      setTopic(finalTopic);
      toast.success("Notes generated successfully!");
    } catch (err) {
      const errorDetail = err.response?.data?.detail || err.message;
      if (errorDetail && (errorDetail.includes("429") || errorDetail.includes("quota"))) {
        toast.error("API Rate Limit Reached! Please try again later.");
      } else {
        toast.error(`Failed to generate notes: ${errorDetail}`);
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
    <PageLayout>
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-zinc-100 mb-2 tracking-tight flex items-center gap-3">
            <FileText className="w-8 h-8 text-violet-500" />
            AI Study Notes
          </h1>
          <p className="text-zinc-400">
            Generate comprehensive notes, flashcards, and mind maps from your content.
          </p>
        </div>

        {/* Input Section */}
        <Card className="mb-8 p-6 border-zinc-800 bg-zinc-900/40">
          <div className="flex flex-col sm:flex-row gap-3">
            <Input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && generateNotes()}
              placeholder="Enter a topic (e.g., React Hooks, Neural Networks...)"
              className="flex-1 bg-zinc-950 border-zinc-800"
              disabled={loading}
            />
            <Button
              variant="gradient"
              onClick={() => generateNotes()}
              disabled={loading}
              className="whitespace-nowrap"
            >
              {loading ? (
                <>
                  <PulseLoader color="#ffffff" size={6} className="mr-2" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Generate Notes
                </>
              )}
            </Button>
          </div>

          {/* Suggested Topics */}
          {suggestedTopics.length > 0 && !notes && (
            <div className="mt-6">
              <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                <Lightbulb className="w-3 h-3" />
                Suggested Topics
              </h3>
              <div className="flex flex-wrap gap-2">
                {suggestedTopics.slice(0, 8).map((item, i) => {
                  const conceptText = typeof item === 'string' ? item : item.title || item.name || item;
                  return (
                    <button
                      key={i}
                      onClick={() => handleSuggestionClick(item)}
                      className="px-3 py-1.5 rounded-lg text-sm bg-zinc-800/50 text-zinc-400 hover:text-violet-300 hover:bg-violet-500/10 border border-zinc-700 hover:border-violet-500/30 transition-all"
                    >
                      {conceptText}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </Card>

        {loading && (
          <div className="text-center py-20">
            <Loader />
            <p className="text-zinc-400 mt-4 text-sm animate-pulse">Analyzing content & generating notes...</p>
          </div>
        )}

        {notes && !loading && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-700">

            {/* Summary */}
            <Card className="p-8 border-l-4 border-l-violet-500">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-violet-400" />
                  Summary
                </h2>
                <div className="flex gap-2">
                  <Badge variant="warning" className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {notes.estimated_study_time} min
                  </Badge>
                  <Badge variant="danger" className="flex items-center gap-1">
                    <BarChart3 className="w-3 h-3" />
                    {notes.difficulty_level}
                  </Badge>
                </div>
              </div>
              <div className="prose prose-invert prose-zinc max-w-none">
                <p className="text-zinc-300 leading-relaxed text-base">
                  {notes.summary}
                </p>
              </div>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Key Points */}
              <Card className="p-6">
                <h2 className="text-lg font-bold text-zinc-100 mb-4 flex items-center gap-2">
                  <Target className="w-5 h-5 text-emerald-400" />
                  Key Points
                </h2>
                <ul className="space-y-3">
                  {notes.key_points && notes.key_points.map((point, i) => {
                    const pointText = typeof point === 'string' ? point : point.point || point.text;
                    return (
                      <li key={i} className="flex gap-3 text-sm text-zinc-300">
                        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-xs font-bold mt-0.5">
                          {i + 1}
                        </span>
                        <span>{pointText}</span>
                      </li>
                    );
                  })}
                </ul>
              </Card>

              {/* Definitions */}
              <Card className="p-6">
                <h2 className="text-lg font-bold text-zinc-100 mb-4 flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-blue-400" />
                  Definitions
                </h2>
                <div className="space-y-3">
                  {notes.definitions && (Array.isArray(notes.definitions) ? notes.definitions : Object.entries(notes.definitions)).map((item, i) => {
                    const term = Array.isArray(notes.definitions) ? (item.term || item.word) : item[0];
                    const def = Array.isArray(notes.definitions) ? (item.definition || item.meaning) : item[1];
                    return (
                      <div key={i} className="p-3 rounded-lg bg-zinc-800/30 border border-zinc-800">
                        <span className="font-bold text-blue-300 text-sm block mb-1">{term}</span>
                        <span className="text-zinc-400 text-xs leading-relaxed">{def}</span>
                      </div>
                    )
                  })}
                </div>
              </Card>
            </div>

            {/* Flashcards */}
            {notes.flashcards && notes.flashcards.length > 0 && (
              <Card className="p-8 bg-gradient-to-br from-zinc-900 to-zinc-950 border-violet-500/20">
                <h2 className="text-xl font-bold text-zinc-100 mb-6 flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-violet-400" />
                  Flashcards
                </h2>

                <div className="max-w-2xl mx-auto">
                  <div className="aspect-[16/9] mb-8 relative perspective-1000">
                    <div
                      className={`w-full h-full transition-all duration-500 transform-style-3d cursor-pointer ${showAnswer ? 'rotate-y-180' : ''}`}
                      onClick={() => setShowAnswer(!showAnswer)}
                    >
                      {/* Front */}
                      <div className={`absolute inset-0 backface-hidden bg-zinc-800 rounded-2xl p-8 flex flex-col items-center justify-center text-center border border-zinc-700 shadow-xl ${showAnswer ? 'invisible' : 'visible'}`}>
                        <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-4">Question</span>
                        <p className="text-xl md:text-2xl font-medium text-zinc-100">
                          {notes.flashcards[flashcardIndex].question}
                        </p>
                        <span className="absolute bottom-4 text-xs text-zinc-500">Click to flip</span>
                      </div>

                      {/* Back */}
                      <div className={`absolute inset-0 backface-hidden bg-violet-900/20 rounded-2xl p-8 flex flex-col items-center justify-center text-center border border-violet-500/30 shadow-xl rotate-y-180 ${showAnswer ? 'visible' : 'invisible'}`}>
                        <span className="text-xs font-bold text-violet-400 uppercase tracking-wider mb-4">Answer</span>
                        <p className="text-lg md:text-xl text-violet-100">
                          {notes.flashcards[flashcardIndex].answer}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between gap-4">
                    <Button variant="secondary" onClick={prevFlashcard}>
                      <ChevronLeft className="w-4 h-4 mr-2" />
                      Prev
                    </Button>
                    <span className="text-sm font-mono text-zinc-500">
                      {flashcardIndex + 1} / {notes.flashcards.length}
                    </span>
                    <Button variant="secondary" onClick={nextFlashcard}>
                      Next
                      <ChevronRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                </div>
              </Card>
            )}

            {/* Mind Map */}
            {notes.mind_map && (
              <Card className="p-6">
                <h2 className="text-lg font-bold text-zinc-100 mb-6 flex items-center gap-2">
                  <Brain className="w-5 h-5 text-pink-400" />
                  Mind Map
                </h2>
                <div className="flex flex-col items-center">
                  <div className="px-6 py-3 bg-zinc-800 rounded-xl border border-zinc-700 text-zinc-100 font-bold mb-8 shadow-lg">
                    {notes.mind_map.central_topic}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
                    {notes.mind_map.branches && notes.mind_map.branches.map((branch, i) => (
                      <div key={i} className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800 hover:border-pink-500/30 transition-colors text-center">
                        <h3 className="font-bold text-pink-300 mb-2 text-sm">{branch.title}</h3>
                        <p className="text-zinc-500 text-xs">{branch.details}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            )}
          </div>
        )}
      </div>
    </PageLayout>
  );
}
