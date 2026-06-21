'use client';

import { ScoreBreakdown } from '@/types/audit';
import {
  formatCategoryName,
  getBarColor,
  getCategoryColor,
  getCategoryDescription,
} from '@/lib/report-utils';

interface CategoryChapterProps {
  category: string;
  data: ScoreBreakdown;
  chapterIndex: number;
}

export function CategoryChapter({ category, data, chapterIndex }: CategoryChapterProps) {
  const pct = data.percentage ?? 0;
  const subScores = data.sub_scores ? Object.entries(data.sub_scores) : [];
  const pageScores = data.page_scores ?? [];

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600 mb-2">
        Category {chapterIndex}
      </p>
      <h2 className="font-display text-2xl md:text-3xl font-bold text-stone-900 mb-2">
        {formatCategoryName(category)}
      </h2>
      <p className="text-sm text-stone-600 mb-6 leading-relaxed">
        {getCategoryDescription(category)}
      </p>

      {data.applicability && (
        <div className="mb-6 p-3 rounded-lg bg-indigo-50/70 border border-indigo-100">
          <p className="text-xs font-bold uppercase tracking-wider text-indigo-700 mb-1">
            {data.applicability} applicability
          </p>
          <p className="text-sm text-stone-700 leading-relaxed">
            {data.applicability_reason}
          </p>
        </div>
      )}

      <div className="flex items-end justify-between mb-2">
        <span className={`text-4xl font-bold tabular-nums ${getCategoryColor(pct)}`}>
          {data.score}
          <span className="text-lg text-stone-400 font-normal">/{data.max}</span>
        </span>
        <span className={`text-lg font-semibold ${getCategoryColor(pct)}`}>
          {pct.toFixed(1)}%
        </span>
      </div>
      <div className="w-full bg-stone-200 rounded-full h-3 mb-8">
        <div
          className={`h-3 rounded-full transition-all ${getBarColor(pct)}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {subScores.length > 0 && (
        <div className="mb-8">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-stone-500 mb-3">
            Sub-scores
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {subScores.map(([sub, score]) => (
              <div
                key={sub}
                className="flex justify-between items-center px-3 py-2 rounded-md bg-white/70 border border-stone-200/60"
              >
                <span className="text-sm text-stone-600">{formatCategoryName(sub)}</span>
                <span className="text-sm font-bold text-stone-800 tabular-nums">{score}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.best_page && data.worst_page && (
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="p-3 rounded-lg bg-emerald-50/80 border border-emerald-200/50">
            <p className="text-xs font-semibold text-emerald-700">Best</p>
            <p className="text-lg font-bold text-emerald-800">{data.best_page.score.toFixed(1)}</p>
            <p className="text-xs text-stone-500 truncate">{data.best_page.url}</p>
          </div>
          <div className="p-3 rounded-lg bg-rose-50/80 border border-rose-200/50">
            <p className="text-xs font-semibold text-rose-700">Worst</p>
            <p className="text-lg font-bold text-rose-800">{data.worst_page.score.toFixed(1)}</p>
            <p className="text-xs text-stone-500 truncate">{data.worst_page.url}</p>
          </div>
        </div>
      )}

      {pageScores.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-stone-500 mb-3">
            Per-page breakdown
          </h3>
          <div className="flex gap-3 overflow-x-auto pb-2 snap-x snap-mandatory scrollbar-thin">
            {[...pageScores]
              .sort((a, b) => b.score - a.score)
              .map((page, i) => (
                <div
                  key={i}
                  className="snap-start shrink-0 w-56 p-3 rounded-lg bg-white/80 border border-stone-200/60"
                >
                  <a
                    href={page.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-indigo-600 hover:underline line-clamp-2 mb-2 block"
                  >
                    {page.url}
                  </a>
                  <div className="flex justify-between items-center mb-1">
                    <span className={`text-sm font-bold ${getCategoryColor(page.percentage)}`}>
                      {page.score.toFixed(1)}/{data.max}
                    </span>
                    <span className="text-xs text-stone-500">{page.percentage.toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-stone-200 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full ${getBarColor(page.percentage)}`}
                      style={{ width: `${page.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
