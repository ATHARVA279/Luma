import React from 'react';
import { Target, ArrowRight } from 'lucide-react';
import Card from './ui/Card';
import Badge from './ui/Badge';

export default function ConceptCard({ concept }) {
  const name = typeof concept === 'string' ? concept : concept.name || concept.title;
  const extractedAt = typeof concept === 'object' && concept.extracted_at
    ? new Date(concept.extracted_at).toLocaleDateString()
    : null;

  return (
    <Card hover className="group h-full flex flex-col justify-between p-5 border-zinc-800/50 hover:border-violet-500/30">
      <div>
        <div className="flex justify-between items-start mb-3">
          <div className="p-2 bg-violet-500/10 rounded-lg group-hover:bg-violet-500/20 transition-colors">
            <Target className="w-5 h-5 text-violet-400" strokeWidth={2} />
          </div>
          {extractedAt && (
            <span className="text-xs text-zinc-500 font-mono">{extractedAt}</span>
          )}
        </div>

        <h3 className="text-lg font-semibold text-zinc-200 group-hover:text-violet-300 transition-colors mb-2">
          {name}
        </h3>
      </div>

      <div className="flex items-center text-sm text-zinc-500 group-hover:text-violet-400 transition-colors mt-4 font-medium">
        Generate Notes
        <ArrowRight className="w-4 h-4 ml-2 transform group-hover:translate-x-1 transition-transform" />
      </div>
    </Card>
  );
}
