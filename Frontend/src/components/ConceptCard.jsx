import { Lightbulb, ArrowRight } from "lucide-react";

export default function ConceptCard({ concept }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 hover:border-slate-700 transition-all cursor-pointer group">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-600 to-red-600 flex items-center justify-center flex-shrink-0">
          <Lightbulb className="w-5 h-5 text-white" strokeWidth={2} />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-white mb-1">
            {typeof concept === 'string' ? concept : concept.title || concept.name || concept}
          </h3>
          {typeof concept === 'object' && concept.description && (
            <p className="text-slate-400 text-xs mb-2 line-clamp-2">{concept.description}</p>
          )}
          <div className="flex items-center gap-1.5 text-orange-400 text-xs">
            <span>Explore</span>
            <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" strokeWidth={2} />
          </div>
        </div>
      </div>
    </div>
  );
}
