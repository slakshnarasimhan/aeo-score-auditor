'use client';

import { GEOScore } from '@/types/audit';
import { formatCategoryName } from '@/lib/report-utils';
import { ScoreRing } from '../ScoreRing';

interface GeoChapterProps {
  geoScore: GEOScore;
}

function getComponentColor(pct: number): string {
  if (pct >= 70) return 'bg-emerald-500';
  if (pct >= 50) return 'bg-amber-500';
  return 'bg-rose-500';
}

export function GeoChapter({ geoScore }: GeoChapterProps) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-600 mb-2">
        Generative Engine Optimization
      </p>
      <h2 className="font-display text-2xl md:text-3xl font-bold text-stone-900 mb-2">
        GEO Score
      </h2>
      <p className="text-sm text-stone-600 mb-6">
        Brand inclusion readiness for AI systems — {geoScore.brand_name} across{' '}
        {geoScore.pages_analyzed} pages
      </p>

      <div className="flex flex-col sm:flex-row items-center gap-6 mb-8">
        <ScoreRing score={geoScore.geo_score} label="GEO" />
        <p className="text-sm text-stone-700 leading-relaxed italic flex-1">
          {geoScore.summary}
        </p>
      </div>

      <h3 className="text-xs font-semibold uppercase tracking-wider text-stone-500 mb-3">
        Components
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
        {Object.entries(geoScore.components).map(([key, comp]) => {
          const pct = (comp.score / comp.max) * 100;
          return (
            <div key={key} className="p-3 rounded-lg bg-white/70 border border-stone-200/60">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-stone-700">
                  {formatCategoryName(key)}
                </span>
                <span className="text-sm font-bold text-stone-900 tabular-nums">
                  {comp.score}/{comp.max}
                </span>
              </div>
              <div className="w-full bg-stone-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${getComponentColor(pct)}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="p-3 rounded-lg bg-violet-50/80 border border-violet-200/50">
        <p className="text-xs text-violet-800 leading-relaxed">
          GEO Score estimates brand inclusion readiness for AI systems. It does not predict
          rankings or guarantee citations.
        </p>
      </div>
    </div>
  );
}
