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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 p-8 mb-8 shadow-2xl">
          <div className="absolute inset-0 bg-black/10"></div>
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-12 h-12 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-4xl font-bold text-white tracking-tight">Knowledge Quiz</h1>
            </div>
            <p className="text-xl text-white/90 font-medium">
              Test your understanding with AI-generated questions
            </p>
          </div>
        </div>

        {showSuggestions && concepts.length > 0 && (
          <div className="glass-effect rounded-2xl p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <Target className="w-5 h-5 text-emerald-400" />
                <span>Select Topics for Quiz</span>
                <span className="text-sm text-gray-400">({selectedTopics.length} selected)</span>
              </h3>
              <div className="flex gap-2">
                <button
                  onClick={selectAllTopics}
                  className="text-sm bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  Select All
                </button>
                <button
                  onClick={clearAllTopics}
                  className="text-sm bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
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
                    className={`p-3 rounded-xl text-sm transition-all border-2 ${
                      isSelected 
                        ? 'bg-emerald-600 border-emerald-500 text-white' 
                        : 'glass-effect border-emerald-500/30 text-gray-300 hover:border-emerald-500/50'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {isSelected ? (
                        <Check className="w-4 h-4 text-white" />
                      ) : (
                        <div className="w-4 h-4 rounded border-2 border-gray-400" />
                      )}
                      <span className="line-clamp-1 text-left flex-1">{conceptText}</span>
                    </div>
                  </button>
                );
              })}
            </div>
            <p className="text-gray-400 text-sm">
              💡 Select topics you want to be tested on. Questions will cover selected topics.
            </p>
          </div>
        )}

        <div className="glass-effect rounded-2xl p-6 mb-6">
          <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
            <div>
              <h3 className="font-semibold text-white mb-1">Generate Quiz</h3>
              <p className="text-gray-400 text-sm">Choose number of questions</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => startQuiz(5)}
                disabled={loading}
                className="gradient-success hover:shadow-lg hover:shadow-emerald-500/50 text-white px-6 py-3 rounded-xl font-semibold disabled:opacity-50 transition-all"
              >
                Quick (5 Q)
              </button>
              <button
                onClick={() => startQuiz(10)}
                disabled={loading}
                className="gradient-success hover:shadow-lg hover:shadow-emerald-500/50 text-white px-6 py-3 rounded-xl font-semibold disabled:opacity-50 transition-all"
              >
                Standard (10 Q)
              </button>
              <button
                onClick={() => startQuiz(15)}
                disabled={loading}
                className="gradient-success hover:shadow-lg hover:shadow-emerald-500/50 text-white px-6 py-3 rounded-xl font-semibold disabled:opacity-50 transition-all"
              >
                Long (15 Q)
              </button>
            </div>
          </div>
        </div>

        {loading && (
          <div className="glass-effect rounded-2xl p-12 text-center">
            <RingLoader color="#10b981" size={80} />
            <p className="text-gray-400 mt-6">Generating quiz questions with AI...</p>
          </div>
        )}

        {questions.length > 0 && (
          <div className="space-y-6">
            {questions.map((q, i) => {
              const difficultyColors = {
                easy: 'text-green-400 bg-green-400/10',
                medium: 'text-yellow-400 bg-yellow-400/10',
                hard: 'text-red-400 bg-red-400/10'
              };
              const typeLabels = {
                concept: '📚 Concept',
                application: '⚙️ Application',
                scenario: '🎯 Scenario',
                comparison: '⚖️ Comparison'
              };
              
              return (
                <div key={i} className={`glass-effect rounded-2xl p-6 transition-all ${
                  submitted ? (isCorrect(i) ? 'border-2 border-emerald-500' : 'border-2 border-red-500') : 'border border-white/10'
                }`}>
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="flex items-start gap-3 flex-1">
                      <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-600 to-teal-600 flex items-center justify-center text-white font-bold">
                        {i + 1}
                      </span>
                      <p className="font-semibold text-white flex-1">
                        {q.question}
                      </p>
                    </div>
                    <div className="flex gap-2 flex-shrink-0">
                      {q.difficulty && (
                        <span className={`text-xs px-3 py-1 rounded-full font-medium ${difficultyColors[q.difficulty] || 'text-gray-400 bg-gray-400/10'}`}>
                          {q.difficulty}
                        </span>
                      )}
                      {q.type && (
                        <span className="text-xs px-3 py-1 rounded-full font-medium text-blue-400 bg-blue-400/10">
                          {typeLabels[q.type] || q.type}
                        </span>
                      )}
                    </div>
                  </div>
                
                <div className="space-y-2 pl-11">
                  {q.options.map((opt, idx) => (
                    <label
                      key={idx}
                      className={`flex items-center p-4 rounded-xl border cursor-pointer transition-all ${
                        submitted && opt.charAt(0) === q.answer 
                          ? 'bg-emerald-900/30 border-emerald-500 ring-2 ring-emerald-500/50' 
                          : submitted && answers[i] === opt && opt.charAt(0) !== q.answer 
                          ? 'bg-red-900/30 border-red-500' 
                          : 'border-gray-700 hover:bg-white/5'
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
                      <span className={`flex-1 ${
                        submitted && opt.charAt(0) === q.answer ? 'font-semibold text-emerald-300' : 'text-gray-300'
                      }`}>
                        {opt}
                      </span>
                      {submitted && opt.charAt(0) === q.answer && (
                        <Check className="w-5 h-5 text-emerald-400" />
                      )}
                    </label>
                  ))}
                </div>

                {submitted && q.explanation && (
                  <div className="mt-4 ml-11 glass-effect border border-blue-500/30 rounded-xl p-4 bg-blue-900/10">
                    <p className="text-sm text-blue-300 font-semibold mb-1 flex items-center gap-2">
                      <Lightbulb className="w-4 h-4" />
                      <span>Explanation:</span>
                    </p>
                    <p className="text-sm text-gray-300 whitespace-pre-wrap">{q.explanation}</p>
                  </div>
                )}
              </div>
              );
            })}

            {!submitted && (
              <button
                onClick={submitQuiz}
                className="w-full gradient-success hover:shadow-xl hover:shadow-emerald-500/50 text-white px-8 py-4 rounded-xl font-bold text-lg transition-all transform hover:scale-105"
              >
                Submit Quiz
              </button>
            )}

            {submitted && (
              <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-violet-600 via-purple-600 to-indigo-600 p-8 text-center shadow-2xl">
                <div className="absolute inset-0 bg-black/10"></div>
                <div className="relative z-10">
                  <h3 className="text-3xl font-bold text-white mb-4">🎉 Quiz Complete!</h3>
                  <div className="text-7xl font-bold text-white mb-2">{score}/{questions.length}</div>
                  <div className="text-3xl font-bold text-white/90 mb-6">{Math.round((score/questions.length) * 100)}%</div>
                  <p className="text-white/80 mb-6">
                    {selectedTopics.length > 0 && `Topics: ${selectedTopics.join(', ')}`}
                  </p>
                  <div className="flex gap-4 justify-center">
                    <button
                      onClick={backToTopics}
                      className="glass-effect hover:bg-white/20 text-white px-8 py-3 rounded-xl font-semibold transition-all"
                    >
                      Back to Topics
                    </button>
                    <button
                      onClick={retryQuiz}
                      disabled={loading}
                      className="bg-white text-violet-600 px-8 py-3 rounded-xl font-semibold hover:bg-gray-100 transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? 'Generating...' : 'Try Another Quiz'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
