import { Lightbulb, ArrowRight } from "lucide-react";

export default function ConceptCard({ concept }) {
  return (
    <div className="glass-effect rounded-xl p-5 hover:bg-white/10 transition-all duration-300 border border-white/10 hover:border-violet-500/50 cursor-pointer transform hover:-translate-y-1 hover:shadow-2xl hover:shadow-violet-500/20 group">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
          <Lightbulb className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-violet-300 transition-colors">
            {typeof concept === 'string' ? concept : concept.title || concept.name || concept}
          </h3>
          {typeof concept === 'object' && concept.description && (
            <p className="text-gray-400 text-sm mb-2 line-clamp-2">{concept.description}</p>
          )}
          <div className="flex items-center gap-2 text-violet-400 text-xs font-medium mt-3">
            <span>Click to explore</span>
            <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>
      </div>
    </div>
  );
}
