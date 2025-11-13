import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Link as LinkIcon, Sparkles, Trash2, Rocket, Target, Settings } from "lucide-react";
import { toast } from 'react-toastify';
import { PulseLoader } from 'react-spinners';
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

    const initializeML = async () => {
      setInitializingML(true);
      try {
        await api.get("/warmup");
        setMlReady(true);
      } catch (err) {
        console.log("ML warmup skipped, will initialize on first use");
        setMlReady(true);
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
      
      setExtractedInfo(info);
      setConcepts(extractedConcepts);
      
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
    const topicName = typeof concept === 'string' ? concept : concept.title || concept.name || concept;
    navigate("/notes", { state: { topic: topicName } });
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
                  await api.delete("/clear-store");
                  
                  localStorage.removeItem("extractedConcepts");
                  localStorage.removeItem("extractedInfo");
                  localStorage.removeItem("extractedUrl");
                  setConcepts([]);
                  setExtractedInfo(null);
                  setUrl("");
                  
                  toast.success("All content cleared successfully!");
                } catch (err) {

  return (
    <div className="min-h-screen bg-slate-950 p-4 sm:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Hero Section */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-8 mb-6">
          <div className="flex items-center gap-4 mb-3">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-orange-600 to-red-600 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" strokeWidth={2} />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">
                AI Learning Navigator
              </h1>
              <p className="text-sm text-slate-400 mt-1">
                Transform web content into interactive learning experiences
              </p>
            </div>
          </div>
        </div>

        {initializingML && (
          <div className="bg-slate-900/50 border border-orange-500/30 rounded-xl p-4 mb-6">
            <p className="text-orange-300 text-sm flex items-center gap-2">
              <Settings className="w-4 h-4 animate-spin" />
              Initializing AI models (first time only)...
            </p>
          </div>
        )}

        {/* Extract Section */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-orange-600/20 flex items-center justify-center border border-orange-500/30">
              <LinkIcon className="w-5 h-5 text-orange-400" strokeWidth={2} />
            </div>
            <h2 className="text-xl font-semibold text-white">Extract Content</h2>
          </div>
          <p className="text-slate-400 text-sm mb-4">
            Enter any article, documentation, or educational content URL to begin learning
          </p>
          
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              placeholder="https://example.com/article"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleExtract()}
              className="flex-1 bg-slate-900 text-white border border-slate-700 px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent placeholder-slate-500 transition-all"
            />
            <button
              onClick={handleExtract}
              disabled={loading}
              className="bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-500 hover:to-red-500 text-white font-medium px-6 py-3 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 justify-center"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <PulseLoader color="#ffffff" size={8} />
                  Extracting...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5" strokeWidth={2} />
                  Extract & Learn
                </span>
              )}
            </button>
            {(concepts.length > 0 || extractedInfo) && (
              <button
                onClick={handleClearData}
                disabled={loading}
                className="px-4 py-3 rounded-lg font-medium bg-red-600/10 hover:bg-red-600/20 border border-red-500/30 text-red-400 hover:text-red-300 disabled:opacity-50 transition-all flex items-center gap-2"
                title="Clear all data and start fresh"
              >
                <Trash2 className="w-5 h-5" strokeWidth={2} />
                <span className="hidden sm:inline">Clear</span>
              </button>
            )}
          </div>
        </div>

        {loading && (
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-12 mb-6 text-center">
            <Loader />
            <p className="text-slate-400 mt-4 text-sm">
              Analyzing content with AI... This may take a moment
            </p>
          </div>
        )}

        {concepts.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-orange-600/20 flex items-center justify-center border border-orange-500/30">
                  <Target className="w-5 h-5 text-orange-400" strokeWidth={2} />
                </div>
                <h3 className="text-xl font-semibold text-white">
                  Key Concepts
                </h3>
              </div>
              <div className="text-sm text-slate-400 hidden sm:block">
                Click to generate notes
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {concepts.map((concept, i) => (
                <div 
                  key={i}
                  onClick={() => handleConceptClick(concept)}
                >
                  <ConceptCard concept={concept} />
                </div>
              ))}
            </div>
          </div>
        )}

        {!concepts.length && !loading && !extractedInfo && (
          <div className="text-center py-16">
            <div className="w-16 h-16 mx-auto mb-4 rounded-lg bg-orange-600/20 flex items-center justify-center border border-orange-500/30">
              <Rocket className="w-8 h-8 text-orange-400" strokeWidth={2} />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Ready to Start Learning?</h3>
            <p className="text-slate-400 text-sm max-w-md mx-auto">
              Enter a URL above to extract content and unlock all AI-powered learning features
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
