import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Link, Sparkles, Trash2, BookOpen, MessageCircle, CheckCircle, FileText, LayoutDashboard, GraduationCap } from "lucide-react";
import { toast } from 'react-toastify';
import { ClipLoader } from 'react-spinners';
import api from "../api/backend";
import Loader from "../components/Loader";
import ConceptCard from "../components/ConceptCard";

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [concepts, setConcepts] = useState([]);
  const [extractedInfo, setExtractedInfo] = useState(null);
  const [mlReady, setMlReady] = useState(false);
  const [initializingML, setInitializingML] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const savedConcepts = localStorage.getItem("extractedConcepts");
    const savedInfo = localStorage.getItem("extractedInfo");
    const savedUrl = localStorage.getItem("extractedUrl");
    
    if (savedConcepts) {
      setConcepts(JSON.parse(savedConcepts));
    }
    if (savedInfo) {
      setExtractedInfo(JSON.parse(savedInfo));
    }
    if (savedUrl) {
      setUrl(savedUrl);
    }

    // Warmup ML models on first load
    const initializeML = async () => {
      setInitializingML(true);
      try {
        await api.get("/warmup");
        setMlReady(true);
      } catch (err) {
        console.log("ML warmup skipped, will initialize on first use");
        setMlReady(true); // Continue anyway
      } finally {
        setInitializingML(false);
      }
    };
    initializeML();
  }, []);

  const handleExtract = async () => {
    if (!url.trim()) {
      toast.error("Please enter a valid URL");
      return;
    }
    
    setLoading(true);
    setConcepts([]);
    setExtractedInfo(null);
    
    try {
      toast.info("Extracting content...");
      const res = await api.post("/extract", { url });
      const info = {
        url: res.data.url,
        textLength: res.data.full_length,
        chunksIndexed: res.data.chunks_indexed
      };
      const extractedConcepts = res.data.concepts || [];
      
      // Save to state
      setExtractedInfo(info);
      setConcepts(extractedConcepts);
      
      // Persist to localStorage
      localStorage.setItem("extractedConcepts", JSON.stringify(extractedConcepts));
      localStorage.setItem("extractedInfo", JSON.stringify(info));
      localStorage.setItem("extractedUrl", url);
      
      toast.success(`Successfully extracted ${extractedConcepts.length} concepts!`);
    } catch (err) {
      console.error(err);
      toast.error("Failed to extract content. Please check the URL and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleConceptClick = (concept) => {
    navigate("/learn", { state: { concept } });
  };

  const handleGenerateNotes = (concept) => {
    const topicName = typeof concept === 'string' ? concept : concept.title || concept.name || concept;
    navigate("/notes", { state: { topic: topicName } });
  };

  const handleClearData = async () => {
    const confirmClear = () => {
      toast.info(
        <div>
          <p className="font-semibold mb-3">Clear all extracted content?</p>
          <div className="flex gap-2">
            <button
              onClick={async () => {
                toast.dismiss();
                try {
                  // Clear backend vector stores
                  await api.delete("/clear-store");
                  
                  // Clear frontend localStorage
                  localStorage.removeItem("extractedConcepts");
                  localStorage.removeItem("extractedInfo");
                  localStorage.removeItem("extractedUrl");
                  setConcepts([]);
                  setExtractedInfo(null);
                  setUrl("");
                  
                  toast.success("All content cleared successfully!");
                } catch (err) {
                  console.error("Clear error:", err);
                  toast.warning("Failed to clear backend stores, but frontend data was cleared.");
                }
              }}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              Yes, Clear
            </button>
            <button
              onClick={() => toast.dismiss()}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>,
        {
          position: "top-center",
          autoClose: false,
          closeOnClick: false,
          draggable: false,
          closeButton: false,
        }
      );
    };
    confirmClear();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Hero Section */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-violet-600 via-purple-600 to-indigo-600 p-8 md:p-12 mb-8 shadow-2xl">
          <div className="absolute inset-0 bg-black/10"></div>
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
                <GraduationCap className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-4xl md:text-5xl font-bold text-white tracking-tight">
                AI Learning Navigator
              </h1>
            </div>
            <p className="text-xl text-white/90 max-w-2xl font-medium">
              Transform any web content into an interactive learning experience with AI-powered insights
            </p>
          </div>
        </div>

        {initializingML && (
          <div className="glass-effect rounded-2xl p-4 mb-6 border border-blue-500/30">
            <p className="text-blue-300 text-sm flex items-center gap-2">
              <span className="animate-spin">⚙️</span>
              Initializing AI models (first time only)...
            </p>
          </div>
        )}

        {/* Extract Section */}
        <div className="glass-effect rounded-2xl p-6 md:p-8 mb-8 shadow-xl">
          <div className="flex items-center gap-3 mb-4">
            <Link className="w-6 h-6 text-violet-400" />
            <h2 className="text-2xl font-bold text-white">Extract Content</h2>
          </div>
          <p className="text-gray-400 mb-6">
            Enter any article, documentation, or educational content URL to begin learning
          </p>
          
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              placeholder="https://example.com/article"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleExtract()}
              className="flex-1 bg-gray-800/50 text-white border border-gray-700 px-5 py-4 rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent placeholder-gray-500 transition-all"
            />
            <button
              onClick={handleExtract}
              disabled={loading}
              className="gradient-primary hover:shadow-lg hover:shadow-violet-500/50 text-white px-8 py-4 rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <ClipLoader color="#ffffff" size={16} />
                  Extracting...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Extract & Learn
                </span>
              )}
            </button>
            {(concepts.length > 0 || extractedInfo) && (
              <button
                onClick={handleClearData}
                disabled={loading}
                className="bg-red-600/80 hover:bg-red-600 text-white px-6 py-4 rounded-xl font-semibold disabled:opacity-50 transition-all flex items-center gap-2"
                title="Clear all data and start fresh"
              >
                <Trash2 className="w-4 h-4" />
                Clear
              </button>
            )}
          </div>
        </div>

        {loading && (
          <div className="glass-effect rounded-2xl p-12 mb-8 text-center">
            <Loader />
            <p className="text-gray-400 mt-4 font-medium">
              Analyzing content with AI... This may take a moment
            </p>
          </div>
        )}

        {concepts.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🎯</span>
                <h3 className="text-2xl font-bold text-white">
                  Key Concepts
                </h3>
              </div>
              <div className="text-sm text-gray-400">
                Click to learn • Right-click for notes
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {concepts.map((concept, i) => (
                <div key={i} className="group relative">
                  <div 
                    onClick={() => handleConceptClick(concept)} 
                    className="cursor-pointer"
                  >
                    <ConceptCard concept={concept} />
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleGenerateNotes(concept);
                    }}
                    className="absolute top-3 right-3 bg-violet-600 hover:bg-violet-700 text-white p-2 rounded-lg opacity-0 group-hover:opacity-100 transition-all transform hover:scale-110 shadow-lg"
                    title="Generate notes for this concept"
                  >
                    📝
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {!concepts.length && !loading && !extractedInfo && (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">🚀</div>
            <h3 className="text-2xl font-bold text-white mb-2">Ready to Start Learning?</h3>
            <p className="text-gray-400 max-w-md mx-auto">
              Enter a URL above to extract content and unlock all AI-powered learning features
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
