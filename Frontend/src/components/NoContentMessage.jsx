import { Link } from "react-router-dom";
import { Lock, Home, ArrowRight } from "lucide-react";

export default function NoContentMessage({ feature = "this feature" }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6 flex items-center justify-center">
      <div className="max-w-2xl mx-auto text-center">
        <div className="glass-effect rounded-3xl p-12 border border-violet-500/30">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center mx-auto mb-6">
            <Lock className="w-10 h-10 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">
            Content Not Found
          </h2>
          <p className="text-gray-400 text-lg mb-8">
            You need to extract content first before using {feature}.
          </p>
          <div className="space-y-4">
            <p className="text-gray-500 text-sm">
              Extract content from any article, documentation, or educational website to unlock all AI-powered learning features.
            </p>
            <Link
              to="/"
              className="inline-flex items-center gap-2 gradient-primary hover:shadow-lg hover:shadow-violet-500/50 text-white px-8 py-4 rounded-xl font-semibold transition-all transform hover:scale-105"
            >
              <Home className="w-5 h-5" />
              <span>Go to Home & Extract Content</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
        
        <div className="mt-8 text-gray-500 text-sm">
          <p className="mb-2">💡 Quick Start:</p>
          <ol className="text-left max-w-md mx-auto space-y-1">
            <li>1. Go to Home page</li>
            <li>2. Enter any educational URL</li>
            <li>3. Click "Extract & Learn"</li>
            <li>4. Explore AI-powered features</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
