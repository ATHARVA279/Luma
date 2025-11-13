import { useState } from "react";
import { CheckCircle, Target, Lightbulb, Check, X } from "lucide-react";
import { toast } from 'react-toastify';
import { RingLoader } from 'react-spinners';
import api from "../api/backend";
import Loader from "../components/Loader";
import NoContentMessage from "../components/NoContentMessage";
import { hasExtractedContent, getExtractedConcepts } from "../utils/contentCheck";

export default function Quiz() {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [score, setScore] = useState(0);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [selectedTopics, setSelectedTopics] = useState([]);

  // Check if content exists
  if (!hasExtractedContent()) {
    return <NoContentMessage feature="the Quiz feature" />;
  }

  const concepts = getExtractedConcepts();

  const toggleTopic = (topic) => {
    const topicText = typeof topic === 'string' ? topic : topic.title || topic.name || topic;
    setSelectedTopics(prev => 
      prev.includes(topicText) 
        ? prev.filter(t => t !== topicText)
        : [...prev, topicText]
    );
  };

  const selectAllTopics = () => {
    const allTopics = concepts.map(item => 
      typeof item === 'string' ? item : item.title || item.name || item
    );
    setSelectedTopics(allTopics);
  };

  const clearAllTopics = () => {
    setSelectedTopics([]);
  };

  const startQuiz = async (count = 10) => {
    if (selectedTopics.length === 0) {
      toast.warning("Please select at least one topic for the quiz");
      setShowSuggestions(true);
      setQuestions([]);
      setSubmitted(false);
      return;
    }

    setLoading(true);
    setQuestions([]);
    setAnswers({});
    setSubmitted(false);
    setScore(0);
    setShowSuggestions(false);
    
    try {
      toast.info("Generating quiz questions...");
      const res = await api.post('/quiz/generate', { 
        count, 
        topics: selectedTopics 
      });
      setQuestions(res.data.questions || []);
      toast.success(`Quiz ready with ${count} questions!`);
    } catch (err) {
      console.error(err);
      toast.error("Failed to generate quiz. Please extract content from a URL first.");
      setShowSuggestions(true);
    } finally {
      setLoading(false);
    }
  };

  const retryQuiz = () => {
    const questionCount = questions.length;
    setQuestions([]);
    setAnswers({});
    setSubmitted(false);
    setScore(0);
    startQuiz(questionCount);
  };

  const backToTopics = () => {
    setQuestions([]);
    setAnswers({});
    setSubmitted(false);
    setScore(0);
    setShowSuggestions(true);
  };

  const submitQuiz = () => {
    let correctCount = 0;
    questions.forEach((q, i) => {
      const userAnswer = answers[i];
      const correctLetter = q.answer;
      const userLetter = userAnswer?.charAt(0);
      
      if (userAnswer === correctLetter) {
        correctCount++;
      }
    });
    setScore(correctCount);
    setSubmitted(true);
    
    const percentage = Math.round((correctCount / questions.length) * 100);
    if (percentage >= 80) {
      toast.success(`Excellent! You scored ${percentage}%`);
    } else if (percentage >= 60) {
      toast.info(`Good job! You scored ${percentage}%`);
    } else {
      toast.warning(`You scored ${percentage}%. Keep studying!`);
    }
  };

  const isCorrect = (questionIndex) => {
    const q = questions[questionIndex];
    const userAnswer = answers[questionIndex];
    if (!userAnswer) return null;
    
    const userLetter = userAnswer.charAt(0);
    return userLetter === q.answer;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-600 to-red-600 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-white" strokeWidth={2} />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-white">
                AI Quiz Generator
              </h1>
              <p className="text-sm text-slate-400">
                Test your understanding with AI-generated questions
              </p>
            </div>
          </div>
        </div>

        {showSuggestions && concepts.length > 0 && (
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 mb-6">
            <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <div className="w-10 h-10 rounded-lg bg-orange-600/20 flex items-center justify-center border border-orange-500/30">
                  <Target className="w-5 h-5 text-orange-400" strokeWidth={2} />
                </div>
                <span>Select Topics for Quiz</span>
                <span className="text-sm text-slate-400">({selectedTopics.length} selected)</span>
              </h3>
              <div className="flex gap-2">
                <button
                  onClick={selectAllTopics}
                  className="text-sm bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors font-medium"
                >
                  Select All
                </button>
                <button
                  onClick={clearAllTopics}
                  className="text-sm bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg transition-colors font-medium"
                >
                  Clear All
                </button>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-4">
              {concepts.map((item, i) => {
                const conceptText = typeof item === 'string' ? item : item.title || item.name || item;
                const isSelected = selectedTopics.includes(conceptText);
                return (
                  <button
                    key={i}
                    onClick={() => toggleTopic(item)}
                    className={`p-3 rounded-lg text-sm transition-all border ${
                      isSelected 
                        ? 'bg-gradient-to-br from-orange-600 to-red-600 border-orange-500 text-white' 
                        : 'bg-slate-800/50 border-slate-700 text-slate-300 hover:border-orange-500/50'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {isSelected ? (
                        <Check className="w-4 h-4 text-white" strokeWidth={2} />
                      ) : (
                        <div className="w-4 h-4 rounded border-2 border-slate-500" />
                      )}
                      <span className="line-clamp-1 text-left flex-1">{conceptText}</span>
                    </div>
                  </button>
                );
              })}
            </div>
            <p className="text-slate-400 text-sm flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-orange-400" strokeWidth={2} />
              Select topics you want to be tested on. Questions will cover selected topics.
            </p>
          </div>
        )}

        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 mb-6">
          <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
            <div>
              <h3 className="font-semibold text-white mb-1">Generate Quiz</h3>
              <p className="text-slate-400 text-sm">Choose number of questions</p>
            </div>
            <div className="flex gap-3 flex-wrap">
              <button
                onClick={() => startQuiz(5)}
                disabled={loading}
                className="bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-500 hover:to-red-500 text-white px-6 py-3 rounded-lg font-medium disabled:opacity-50 transition-all"
              >
                Quick (5 Q)
              </button>
              <button
                onClick={() => startQuiz(10)}
                disabled={loading}
                className="bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-500 hover:to-red-500 text-white px-6 py-3 rounded-lg font-medium disabled:opacity-50 transition-all"
              >
                Standard (10 Q)
              </button>
              <button
                onClick={() => startQuiz(15)}
                disabled={loading}
                className="bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-500 hover:to-red-500 text-white px-6 py-3 rounded-lg font-medium disabled:opacity-50 transition-all"
              >
                Long (15 Q)
              </button>
            </div>
          </div>
        </div>

        {loading && (
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-12 text-center">
            <Loader />
            <p className="text-slate-400 mt-6 text-sm">Generating quiz questions with AI...</p>
          </div>
        )}

        {questions.length > 0 && (
          <div className="space-y-6">
            {questions.map((q, i) => {
              const difficultyColors = {
                easy: 'text-green-400 bg-green-400/10 border-green-500/20',
                medium: 'text-yellow-400 bg-yellow-400/10 border-yellow-500/20',
                hard: 'text-red-400 bg-red-400/10 border-red-500/20'
              };
              const typeLabels = {
                concept: 'Concept',
                application: 'Application',
                scenario: 'Scenario',
                comparison: 'Comparison'
              };
              
              return (
                <div key={i} className={`bg-slate-900/50 rounded-xl p-6 transition-all ${
                  submitted ? (isCorrect(i) ? 'border-2 border-green-500' : 'border-2 border-red-500') : 'border border-slate-800'
                }`}>
                  <div className="flex items-start justify-between gap-3 mb-4 flex-wrap">
                    <div className="flex items-start gap-3 flex-1">
                      <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-orange-600 to-red-600 flex items-center justify-center text-white font-bold text-sm">
                        {i + 1}
                      </span>
                      <p className="font-semibold text-white flex-1 text-sm">
                        {q.question}
                      </p>
                    </div>
                    <div className="flex gap-2 flex-shrink-0 flex-wrap">
                      {q.difficulty && (
                        <span className={`text-xs px-3 py-1 rounded-lg font-medium border ${difficultyColors[q.difficulty] || 'text-slate-400 bg-slate-400/10 border-slate-500/20'}`}>
                          {q.difficulty}
                        </span>
                      )}
                      {q.type && (
                        <span className="text-xs px-3 py-1 rounded-lg font-medium text-orange-400 bg-orange-400/10 border border-orange-500/20">
                          {typeLabels[q.type] || q.type}
                        </span>
                      )}
                    </div>
                  </div>
                
                <div className="space-y-2 pl-11">
                  {q.options.map((opt, idx) => (
                    <label
                      key={idx}
                      className={`flex items-center p-3 rounded-lg border cursor-pointer transition-all ${
                        submitted && opt.charAt(0) === q.answer 
                          ? 'bg-green-900/30 border-green-500 ring-1 ring-green-500/50' 
                          : submitted && answers[i] === opt && opt.charAt(0) !== q.answer 
                          ? 'bg-red-900/30 border-red-500' 
                          : 'border-slate-700 hover:bg-slate-800/50 hover:border-slate-600'
                      }`}
                    >
                      <input
                        type="radio"
                        name={`q-${i}`}
                        value={opt}
                        checked={answers[i] === opt}
                        onChange={(e) => setAnswers({ ...answers, [i]: e.target.value })}
                        disabled={submitted}
                        className="mr-3 w-4 h-4"
                      />
                      <span className={`flex-1 text-sm ${
                        submitted && opt.charAt(0) === q.answer ? 'font-semibold text-green-300' : 'text-slate-300'
                      }`}>
                        {opt}
                      </span>
                      {submitted && opt.charAt(0) === q.answer && (
                        <Check className="w-5 h-5 text-green-400" strokeWidth={2} />
                      )}
                      {submitted && answers[i] === opt && opt.charAt(0) !== q.answer && (
                        <X className="w-5 h-5 text-red-400" strokeWidth={2} />
                      )}
                    </label>
                  ))}
                </div>

                {submitted && q.explanation && (
                  <div className="mt-4 ml-11 bg-slate-800/30 border border-orange-500/30 rounded-lg p-4">
                    <p className="text-sm text-orange-300 font-semibold mb-1 flex items-center gap-2">
                      <Lightbulb className="w-4 h-4" strokeWidth={2} />
                      <span>Explanation:</span>
                    </p>
                    <p className="text-sm text-slate-300 whitespace-pre-wrap">{q.explanation}</p>
                  </div>
                )}
              </div>
              );
            })}

            {!submitted && (
              <button
                onClick={submitQuiz}
                className="w-full bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-500 hover:to-red-500 text-white px-8 py-4 rounded-lg font-semibold transition-all"
              >
                Submit Quiz
              </button>
            )}

            {submitted && (
              <div className="bg-gradient-to-br from-orange-600 to-red-600 rounded-xl p-8 text-center shadow-2xl">
                <div className="flex items-center justify-center gap-3 mb-4">
                  <CheckCircle className="w-8 h-8 text-white" strokeWidth={2} />
                  <h3 className="text-2xl font-bold text-white">Quiz Complete!</h3>
                </div>
                <div className="text-6xl font-bold text-white mb-2">{score}/{questions.length}</div>
                <div className="text-2xl font-bold text-white/90 mb-6">{Math.round((score/questions.length) * 100)}%</div>
                <p className="text-white/80 mb-6 text-sm">
                  {selectedTopics.length > 0 && `Topics: ${selectedTopics.join(', ')}`}
                </p>
                <div className="flex gap-3 justify-center flex-wrap">
                  <button
                    onClick={backToTopics}
                    className="bg-white/20 hover:bg-white/30 border border-white/30 text-white px-6 py-3 rounded-lg font-medium transition-all"
                  >
                    Back to Topics
                  </button>
                  <button
                    onClick={retryQuiz}
                    disabled={loading}
                    className="bg-white text-orange-600 px-6 py-3 rounded-lg font-medium hover:bg-slate-100 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Generating...' : 'Try Another Quiz'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
