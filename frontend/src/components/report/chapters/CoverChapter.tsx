'use client';

import { format } from 'date-fns';
import { ScoreRing } from '../ScoreRing';
import {
  AuditReportResult,
  ContentClassification,
  isDomainResult,
} from '@/types/audit';
import { getGradeColor, getScoreLabel } from '@/lib/report-utils';

interface CoverChapterProps {
  result: AuditReportResult;
  auditType: 'page' | 'domain';
  sourceUrl: string;
}

function ContentTypeBadge({ classification }: { classification: ContentClassification }) {
  const typeColors: Record<string, string> = {
    experiential: 'bg-purple-100 text-purple-800 border-purple-200',
    informational: 'bg-blue-100 text-blue-800 border-blue-200',
    transactional: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  };
  const colorClass = typeColors[classification.type] || 'bg-stone-100 text-stone-800 border-stone-200';

  return (
    <div className="mt-6 p-4 rounded-lg border border-stone-200/80 bg-white/60">
      <div className="flex flex-wrap items-center gap-2 mb-1">
        <span className="text-xs font-semibold uppercase tracking-wider text-stone-500">Content Type</span>
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase border ${colorClass}`}>
          {classification.type}
        </span>
        <span className="text-xs text-stone-500">({classification.confidence} confidence)</span>
      </div>
      <p className="text-sm text-stone-600 leading-relaxed">{classification.description}</p>
    </div>
  );
}

export function CoverChapter({ result, auditType, sourceUrl }: CoverChapterProps) {
  const title = isDomainResult(result) ? result.domain : sourceUrl;
  const subtitle =
    auditType === 'domain' && isDomainResult(result)
      ? `${result.pages_successful} of ${result.pages_audited} pages audited`
      : 'Single Page Audit';

  return (
    <div className="flex flex-col items-center text-center h-full justify-center">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600 mb-3">
        AEO / GEO Audit Report
      </p>
      <h2 className="font-display text-2xl md:text-3xl font-bold text-stone-900 leading-tight mb-2 break-all">
        {title}
      </h2>
      <p className="text-sm text-stone-500 mb-8">{subtitle}</p>

      <ScoreRing score={result.overall_score} label="AEO Score" />

      <div className="mt-6 flex items-center gap-4">
        <span className={`font-display text-5xl font-bold ${getGradeColor(result.grade)}`}>
          {result.grade}
        </span>
        <div className="text-left border-l border-stone-300 pl-4">
          <p className="text-sm font-medium text-stone-700">{getScoreLabel(result.overall_score)}</p>
          <p className="text-xs text-stone-500">{format(new Date(), 'MMMM d, yyyy')}</p>
        </div>
      </div>

      {result.content_classification && (
        <ContentTypeBadge classification={result.content_classification} />
      )}
    </div>
  );
}
