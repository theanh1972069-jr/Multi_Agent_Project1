import { BookOpen, ExternalLink } from 'lucide-react';
import type { CitationItem } from '../types/api';

interface CitationCardProps {
  citation: CitationItem;
}

export function CitationCard({ citation }: CitationCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 transition-colors hover:border-teal-200 hover:bg-white">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex items-start gap-2.5">
          <span className="inline-flex h-6 min-w-6 shrink-0 items-center justify-center rounded-md bg-teal-600 px-1.5 text-xs font-bold text-white">
            [{citation.index}]
          </span>
          <div>
            <h4 className="text-sm font-semibold text-slate-900">{citation.title}</h4>
            <div className="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-slate-500">
              <span className="inline-flex items-center gap-1 font-medium text-teal-700">
                <BookOpen className="h-3.5 w-3.5" />
                {citation.publisher}
              </span>
              {typeof citation.score === 'number' && citation.score > 0 && (
                <span className="rounded-full bg-slate-200/80 px-2 py-0.5 text-[11px] font-medium text-slate-700">
                  Độ tương đồng: {(citation.score * 100).toFixed(0)}%
                </span>
              )}
            </div>
          </div>
        </div>

        {citation.url && (
          <a
            href={citation.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex shrink-0 items-center gap-1 rounded-lg border border-teal-200 bg-white px-2.5 py-1 text-xs font-medium text-teal-700 hover:bg-teal-50"
          >
            <span>Xem nguồn</span>
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        )}
      </div>

      {citation.snippet && (
        <p className="mt-2.5 text-xs leading-relaxed text-slate-600">{citation.snippet}</p>
      )}
    </div>
  );
}
