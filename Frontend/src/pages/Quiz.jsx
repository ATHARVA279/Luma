import { useState } from "react";
import { CheckCircle, Target, Lightbulb, Check, X, ArrowRight, RotateCcw } from "lucide-react";
import { toast } from 'react-toastify';
import api from "../api/backend";
import Loader from "../components/Loader";
import NoContentMessage from "../components/NoContentMessage";
import { hasExtractedContent, getExtractedConcepts } from "../utils/contentCheck";
import PageLayout from "../components/layout/PageLayout";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Badge from "../components/ui/Badge";

export default function Quiz() {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [score, setScore] = useState(0);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [selectedTopics, setSelectedTopics] = useState([]);

  if (!hasExtractedContent()) {
    return (
      <PageLayout>
        <NoContentMessage feature="the Quiz feature" />
      </PageLayout>
    );
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

    const documentId = localStorage.getItem("extractedDocumentId");
    if (!documentId) {
      toast.error("No document selected. Please extract content first.");
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
        topics: selectedTopics,
        document_id: documentId
      });
      setQuestions(res.data.questions || []);
      toast.success(`Quiz ready with ${count} questions!`);
    } catch (err) {
      console.error(err);
      toast.error("Failed to generate quiz. Please try again.");
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

  const getCorrectIndex = (answerLetter) => {
    if (!answerLetter) return -1;
    return answerLetter.toUpperCase().charCodeAt(0) - 65; // A=0, B=1, etc.
  };

  const submitQuiz = async () => {
    let correctCount = 0;
    questions.forEach((q, i) => {
      const userAnswer = answers[i];
      if (!userAnswer) return;

      const correctIndex = getCorrectIndex(q.answer);
      const userIndex = q.options.indexOf(userAnswer);

      if (userIndex === correctIndex) {
        correctCount++;
      }
    });
    setScore(correctCount);
    setSubmitted(true);

    const percentage = Math.round((correctCount / questions.length) * 100);
    if (percentage >= 80) toast.success(`Excellent! You scored ${percentage}%`);
    else if (percentage >= 60) toast.info(`Good job! You scored ${percentage}%`);
    else toast.warning(`You scored ${percentage}%. Keep studying!`);

    // Save result to backend
    try {
      const documentId = localStorage.getItem("extractedDocumentId");
      await api.post('/quiz/result', {
        score: correctCount,
        total: questions.length,
        topics: selectedTopics,
        document_id: documentId
      });
    } catch (error) {
      console.error("Failed to save quiz result", error);
    }
  };

  const isCorrect = (questionIndex) => {
    const q = questions[questionIndex];
    const userAnswer = answers[questionIndex];
    if (!userAnswer) return null;

    const correctIndex = getCorrectIndex(q.answer);
    const userIndex = q.options.indexOf(userAnswer);

    return userIndex === correctIndex;
  };

  return (
    <PageLayout>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-zinc-100 mb-2 tracking-tight flex items-center gap-3">
            <CheckCircle className="w-8 h-8 text-emerald-500" />
            AI Quiz Generator
          </h1>
          <p className="text-zinc-400">
            Test your understanding with AI-generated questions tailored to your content.
          </p>
        </div>

        {showSuggestions && concepts.length > 0 && (
          <Card className="mb-8 p-6 border-zinc-800 bg-zinc-900/40">
            <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
              <h3 className="text-lg font-semibold text-zinc-200 flex items-center gap-2">
                <Target className="w-5 h-5 text-violet-400" />
                Select Topics
                <Badge variant="default" className="ml-2">{selectedTopics.length} selected</Badge>
              </h3>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={selectAllTopics}>Select All</Button>
                <Button variant="ghost" size="sm" onClick={clearAllTopics}>Clear</Button>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-8">
              {concepts.map((item, i) => {
                const conceptText = typeof item === 'string' ? item : item.title || item.name || item;
                const isSelected = selectedTopics.includes(conceptText);
                return (
                  <button
                    key={i}
                    onClick={() => toggleTopic(item)}
                    className={`
                      p-3 rounded-lg text-sm transition-all border text-left flex items-center gap-2
                      ${isSelected
                        ? 'bg-violet-500/10 border-violet-500/50 text-violet-200'
                        : 'bg-zinc-800/30 border-zinc-800 text-zinc-400 hover:border-zinc-700 hover:text-zinc-300'
                      }
                    `}
                  >
                    <div className={`w-4 h-4 rounded border flex items-center justify-center ${isSelected ? 'border-violet-500 bg-violet-500' : 'border-zinc-600'}`}>
                      {isSelected && <Check className="w-3 h-3 text-white" />}
                    </div>
                    <span className="truncate">{conceptText}</span>
                  </button>
                );
              })}
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-between gap-6 border-t border-zinc-800 pt-6">
              <div>
                <h4 className="text-sm font-medium text-zinc-300 mb-1">Number of Questions</h4>
                <p className="text-xs text-zinc-500">Choose quiz length</p>
              </div>
              <div className="flex gap-3">
                {[5, 10, 15].map(num => (
                  <Button
                    key={num}
                    variant="secondary"
                    onClick={() => startQuiz(num)}
                    disabled={loading}
                  >
                    {num} Questions
                  </Button>
                ))}
              </div>
            </div>
          </Card>
        )}

        {loading && (
          <div className="text-center py-20">
            <Loader />
            <p className="text-zinc-400 mt-6 text-sm animate-pulse">Generating tailored questions...</p>
          </div>
        )}

        {questions.length > 0 && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-700">
            {questions.map((q, i) => {
              const difficultyColors = {
                easy: 'success',
                medium: 'warning',
                hard: 'danger'
              };

              return (
                <Card key={i} className={`p-6 transition-all ${submitted ? (isCorrect(i) ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-red-500/30 bg-red-500/5') : ''}`}>
                  <div className="flex items-start justify-between gap-4 mb-6">
                    <div className="flex gap-4">
                      <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-400 font-bold text-sm border border-zinc-700">
                        {i + 1}
                      </span>
                      <div>
                        <p className="font-medium text-zinc-100 text-lg leading-relaxed">
                          {q.question}
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2 flex-shrink-0">
                      {q.difficulty && <Badge variant={difficultyColors[q.difficulty]}>{q.difficulty}</Badge>}
                      {q.type && <Badge variant="default">{q.type}</Badge>}
                    </div>
                  </div>

                  <div className="space-y-3 pl-12">
                    {q.options.map((opt, idx) => {
                      const isSelected = answers[i] === opt;
                      const correctIndex = getCorrectIndex(q.answer);
                      const isCorrectAnswer = idx === correctIndex;

                      let optionClass = "border-zinc-800 hover:bg-zinc-800/50 hover:border-zinc-700";
                      if (submitted) {
                        if (isCorrectAnswer) optionClass = "border-emerald-500/50 bg-emerald-500/10 text-emerald-200";
                        else if (isSelected && !isCorrectAnswer) optionClass = "border-red-500/50 bg-red-500/10 text-red-200";
                        else optionClass = "border-zinc-800 opacity-50";
                      } else if (isSelected) {
                        optionClass = "border-violet-500 bg-violet-500/10 text-violet-200";
                      }

                      return (
                        <label
                          key={idx}
                          className={`flex items-center p-4 rounded-xl border cursor-pointer transition-all ${optionClass}`}
                        >
                          <input
                            type="radio"
                            name={`q-${i}`}
                            value={opt}
                            checked={isSelected}
                            onChange={(e) => setAnswers({ ...answers, [i]: e.target.value })}
                            disabled={submitted}
                            className="hidden"
                          />
                          <div className={`w-5 h-5 rounded-full border flex items-center justify-center mr-4 ${isSelected || (submitted && isCorrectAnswer)
                            ? 'border-current'
                            : 'border-zinc-600'
                            }`}>
                            {(isSelected || (submitted && isCorrectAnswer)) && <div className="w-2.5 h-2.5 rounded-full bg-current" />}
                          </div>
                          <span className="text-sm font-medium">{opt}</span>
                          {submitted && isCorrectAnswer && <Check className="w-5 h-5 ml-auto text-emerald-500" />}
                          {submitted && isSelected && !isCorrectAnswer && <X className="w-5 h-5 ml-auto text-red-500" />}
                        </label>
                      );
                    })}
                  </div>

                  {submitted && q.explanation && (
                    <div className="mt-6 ml-12 p-4 bg-zinc-900/50 rounded-xl border border-zinc-800">
                      <p className="text-sm text-violet-300 font-semibold mb-1 flex items-center gap-2">
                        <Lightbulb className="w-4 h-4" />
                        Explanation
                      </p>
                      <p className="text-sm text-zinc-400 leading-relaxed">{q.explanation}</p>
                    </div>
                  )}
                </Card>
              );
            })}

            {!submitted && (
              <div className="flex justify-end pt-6">
                <Button
                  variant="gradient"
                  size="lg"
                  onClick={submitQuiz}
                  className="px-12"
                >
                  Submit Quiz
                </Button>
              </div>
            )}

            {submitted && (
              <Card className="bg-zinc-900 border-zinc-800 text-center p-12">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-zinc-800 mb-6">
                  <CheckCircle className="w-8 h-8 text-emerald-500" />
                </div>
                <h3 className="text-3xl font-bold text-zinc-100 mb-2">Quiz Complete!</h3>
                <div className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-indigo-400 mb-2">
                  {score}/{questions.length}
                </div>
                <p className="text-zinc-500 mb-8">
                  You scored {Math.round((score / questions.length) * 100)}%
                </p>

                <div className="flex gap-4 justify-center">
                  <Button variant="secondary" onClick={backToTopics}>
                    Back to Topics
                  </Button>
                  <Button variant="primary" onClick={retryQuiz}>
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Try Again
                  </Button>
                </div>
              </Card>
            )}
          </div>
        )}
      </div>
    </PageLayout>
  );
}
