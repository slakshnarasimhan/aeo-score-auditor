'use client';

import { AuditReportResult, isDomainResult } from '@/types/audit';
import { formatCategoryName, getCategoryDescription } from '@/lib/report-utils';

interface ActionsChapterProps {
  result: AuditReportResult;
}

const CATEGORY_ACTIONS: Record<string, string> = {
  answerability:
    'Add direct Q&A sections, FAQ blocks, and concise answers at the top of key pages.',
  structured_data:
    'Implement Schema.org markup (FAQ, Article, Organization) and validate with Google Rich Results.',
  authority:
    'Add author bios, citations, credentials, and external references to build trust signals.',
  content_quality:
    'Expand thin content, update stale pages, and add unique insights competitors lack.',
  citationability:
    'Include clear facts, statistics, tables, and quotable statements AI can reference.',
  technical:
    'Improve page speed, mobile responsiveness, meta tags, and crawlability.',
  ai_citation:
    'Structure content for AI extraction: clear headings, definitions, and factual statements.',
};

export function ActionsChapter({ result }: ActionsChapterProps) {
  const weakCategories = Object.entries(result.breakdown)
    .filter(([, data]) => (data.percentage ?? 0) < 70)
    .sort((a, b) => (a[1].percentage ?? 0) - (b[1].percentage ?? 0));

  const geoActions =
    isDomainResult(result) && result.geo_score
      ? result.geo_score.recommended_actions
      : [];
  const extractionRecommendations = result.recommendations ?? [];

  const hasActions = extractionRecommendations.length > 0 || weakCategories.length > 0 || geoActions.length > 0;

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600 mb-2">
        Next Steps
      </p>
      <h2 className="font-display text-2xl md:text-3xl font-bold text-stone-900 mb-6">
        Recommended Actions
      </h2>

      {!hasActions && (
        <div className="p-6 rounded-lg bg-emerald-50/80 border border-emerald-200/60 text-center">
          <p className="text-lg font-medium text-emerald-800">Strong performance across the board</p>
          <p className="text-sm text-stone-600 mt-2">
            Maintain content freshness and monitor scores as you publish new pages.
          </p>
        </div>
      )}

      {geoActions.length > 0 && (
        <section className="mb-8">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-violet-600 mb-3">
            GEO Priorities
          </h3>
          <ol className="space-y-3">
            {geoActions.map((action, i) => (
              <li key={i} className="flex gap-3">
                <span className="shrink-0 w-6 h-6 rounded-full bg-violet-100 text-violet-700 text-xs font-bold flex items-center justify-center">
                  {i + 1}
                </span>
                <span className="text-sm text-stone-700 leading-relaxed">{action}</span>
              </li>
            ))}
          </ol>
        </section>
      )}

      {extractionRecommendations.length > 0 && (
        <section className="mb-8">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-600 mb-3">
            Extraction Priorities
          </h3>
          <div className="space-y-4">
            {extractionRecommendations.map((recommendation, i) => (
              <div
                key={`${recommendation.category}-${i}`}
                className="p-4 rounded-lg bg-indigo-50/70 border border-indigo-100"
              >
                <div className="flex justify-between gap-3 mb-1">
                  <h4 className="font-semibold text-stone-800">{recommendation.title}</h4>
                  {recommendation.applicability && (
                    <span className="text-xs font-bold uppercase text-indigo-700">
                      {recommendation.applicability}
                    </span>
                  )}
                </div>
                {recommendation.reason && (
                  <p className="text-xs text-stone-500 mb-2">{recommendation.reason}</p>
                )}
                <ul className="space-y-1">
                  {recommendation.tips.map((tip) => (
                    <li key={tip} className="text-sm text-stone-700 leading-relaxed">
                      {tip}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {extractionRecommendations.length === 0 && weakCategories.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-stone-500 mb-3">
            AEO Improvement Areas
          </h3>
          <div className="space-y-4">
            {weakCategories.map(([category, data]) => (
              <div
                key={category}
                className="p-4 rounded-lg bg-white/70 border border-stone-200/60"
              >
                <div className="flex justify-between items-start mb-1">
                  <h4 className="font-semibold text-stone-800">
                    {formatCategoryName(category)}
                  </h4>
                  <span className="text-sm font-bold text-rose-600 tabular-nums">
                    {(data.percentage ?? 0).toFixed(0)}%
                  </span>
                </div>
                <p className="text-xs text-stone-500 mb-2">{getCategoryDescription(category)}</p>
                <p className="text-sm text-stone-700 leading-relaxed">
                  {CATEGORY_ACTIONS[category] ||
                    `Review and improve ${formatCategoryName(category).toLowerCase()} signals across audited pages.`}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
