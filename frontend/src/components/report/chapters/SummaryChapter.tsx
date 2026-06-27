'use client';

import {
  AuditReportResult,
  isDomainResult,
  ScoreBreakdown,
} from '@/types/audit';
import {
  formatCategoryName,
  getBarColor,
  getCategoryColor,
  getScoreLabel,
} from '@/lib/report-utils';

interface SummaryChapterProps {
  result: AuditReportResult;
}

function CategorySnapshot({
  category,
  data,
}: {
  category: string;
  data: ScoreBreakdown;
}) {
  const pct = data.percentage ?? 0;
  return (
    <div className="flex items-center gap-3 py-2">
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-stone-800 truncate">
          {formatCategoryName(category)}
        </p>
        <div className="mt-1 w-full bg-stone-200 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full transition-all ${getBarColor(pct)}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
      <span className={`text-sm font-bold tabular-nums ${getCategoryColor(pct)}`}>
        {pct.toFixed(0)}%
      </span>
    </div>
  );
}

export function SummaryChapter({ result }: SummaryChapterProps) {
  const categories = Object.entries(result.breakdown || {});
  const sorted = [...categories].sort(
    (a, b) => (b[1].percentage ?? 0) - (a[1].percentage ?? 0)
  );
  const strongest = sorted[0];
  const weakest = sorted[sorted.length - 1];

  const insights: string[] = [
    `Overall performance is ${getScoreLabel(result.overall_score).toLowerCase()} at ${result.overall_score}/100.`,
  ];

  if (strongest) {
    insights.push(
      `Strongest area: ${formatCategoryName(strongest[0])} (${(strongest[1].percentage ?? 0).toFixed(0)}%).`
    );
  }
  if (weakest && weakest[0] !== strongest?.[0]) {
    insights.push(
      `Priority focus: ${formatCategoryName(weakest[0])} (${(weakest[1].percentage ?? 0).toFixed(0)}%).`
    );
  }

  if (isDomainResult(result) && result.best_page && result.worst_page) {
    insights.push(
      `Best page scores ${result.best_page.overall_score}/100; weakest page scores ${result.worst_page.overall_score}/100.`
    );
  }

  if (result.audit_profile) {
    insights.push(
      `Audit profile: ${result.audit_profile.label} focuses on ${result.audit_profile.extraction_goals.slice(0, 4).join(', ')}.`
    );
  }

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600 mb-2">
        Chapter Overview
      </p>
      <h2 className="font-display text-2xl md:text-3xl font-bold text-stone-900 mb-6">
        Executive Summary
      </h2>

      <ul className="space-y-3 mb-8">
        {insights.map((insight, i) => (
          <li key={i} className="flex gap-3 text-stone-700 leading-relaxed">
            <span className="text-indigo-500 font-bold shrink-0">•</span>
            <span>{insight}</span>
          </li>
        ))}
      </ul>

      <h3 className="text-sm font-semibold uppercase tracking-wider text-stone-500 mb-3">
        Category Snapshot
      </h3>
      <div className="space-y-1 divide-y divide-stone-100">
        {sorted.map(([category, data]) => (
          <CategorySnapshot key={category} category={category} data={data} />
        ))}
      </div>

      {result.extraction_goals && result.extraction_goals.length > 0 && (
        <div className="mt-8">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-stone-500 mb-3">
            Extraction Goals
          </h3>
          <div className="flex flex-wrap gap-2">
            {result.extraction_goals.slice(0, 10).map((goal) => (
              <span
                key={goal}
                className="px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100 text-xs font-medium"
              >
                {goal.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {isDomainResult(result) && result.best_page && result.worst_page && (
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-emerald-50/80 border border-emerald-200/60">
            <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700 mb-1">
              Best Page
            </p>
            <p className="text-2xl font-bold text-emerald-800 tabular-nums">
              {result.best_page.overall_score}/100
            </p>
            <p className="text-xs text-stone-600 mt-1 truncate" title={result.best_page.url}>
              {result.best_page.url}
            </p>
          </div>
          <div className="p-4 rounded-lg bg-rose-50/80 border border-rose-200/60">
            <p className="text-xs font-semibold uppercase tracking-wider text-rose-700 mb-1">
              Needs Improvement
            </p>
            <p className="text-2xl font-bold text-rose-800 tabular-nums">
              {result.worst_page.overall_score}/100
            </p>
            <p className="text-xs text-stone-600 mt-1 truncate" title={result.worst_page.url}>
              {result.worst_page.url}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
