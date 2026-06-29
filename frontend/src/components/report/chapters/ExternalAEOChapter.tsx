'use client';

import { ExternalAEOAnalysis, ExternalAEOQuestionResult } from '@/types/audit';

interface ExternalAEOChapterProps {
  analysis: ExternalAEOAnalysis;
}

const providerLabels: Record<string, string> = {
  ollama: 'Ollama',
};

function ScoreTile({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: 'emerald' | 'sky' | 'indigo' | 'stone';
}) {
  const styles = {
    emerald: 'border-emerald-100 bg-emerald-50 text-emerald-800',
    sky: 'border-sky-100 bg-sky-50 text-sky-800',
    indigo: 'border-indigo-100 bg-indigo-50 text-indigo-800',
    stone: 'border-stone-200 bg-stone-50 text-stone-800',
  };
  return (
    <div className={`rounded-lg border p-3 ${styles[tone]}`}>
      <p className="text-xs font-semibold">{label}</p>
      <p className="mt-1 text-2xl font-bold tabular-nums">{value}%</p>
    </div>
  );
}

function QuestionBlock({ question }: { question: ExternalAEOQuestionResult }) {
  const providers = question.providers.filter((provider) => provider.provider !== 'openai');

  return (
    <div className="border-b border-stone-100 py-4 last:border-b-0">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-sm font-semibold leading-snug text-stone-900">
            {question.prompt}
          </p>
          <p className="mt-1 text-xs uppercase tracking-wider text-stone-400">
            {question.journey_label ?? question.journey_stage ?? 'Question'} · {question.intent ?? 'intent'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2 sm:justify-end">
          <span className="rounded border border-emerald-200 bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-800">
            External {question.external_visibility_score}
          </span>
          <span className="rounded border border-stone-200 bg-stone-50 px-2 py-1 text-xs font-semibold text-stone-700">
            Match {question.internal_external_alignment_score}
          </span>
        </div>
      </div>

      <div className="mt-3 grid gap-3">
        {providers.map((provider) => (
          <div key={provider.provider} className="rounded-lg border border-stone-200 bg-stone-50 p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-xs font-bold uppercase tracking-wider text-stone-600">
                {providerLabels[provider.provider] ?? provider.provider}
              </p>
              <div className="flex flex-wrap gap-2 text-[11px] font-semibold">
                <span className={provider.brand_mentioned ? 'text-emerald-700' : 'text-rose-700'}>
                  {provider.brand_mentioned ? 'Brand found' : 'Brand absent'}
                </span>
                <span className={provider.official_site_cited ? 'text-emerald-700' : 'text-stone-500'}>
                  {provider.official_site_cited ? 'Official cited' : 'Official not cited'}
                </span>
              </div>
            </div>
            {provider.error ? (
              <p className="mt-2 text-xs text-rose-700">{provider.error}</p>
            ) : (
              <>
                <p className="mt-2 line-clamp-3 text-xs leading-relaxed text-stone-700">
                  {provider.answer}
                </p>
                {provider.citations.length > 0 && (
                  <p className="mt-2 truncate text-[11px] text-stone-400" title={provider.citations[0].url}>
                    {provider.citations[0].title || provider.citations[0].url}
                  </p>
                )}
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export function ExternalAEOChapter({ analysis }: ExternalAEOChapterProps) {
  const summary = analysis.summary;

  return (
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-600">
        Ollama AEO Validation
      </p>
      <h2 className="mb-3 font-display text-2xl font-bold text-stone-900 md:text-3xl">
        Collective Answer-Engine Visibility
      </h2>
      <p className="mb-6 text-sm leading-relaxed text-stone-600">
        These are the same generated questions tested against the configured Ollama
        validator, then compared with the local website-readiness estimate.
      </p>

      {!analysis.available && (
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          {analysis.reason ?? 'Answer-engine validation was enabled, but no Ollama provider was available.'}
        </div>
      )}

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <ScoreTile label="Visibility" value={summary.external_visibility_score} tone="emerald" />
        <ScoreTile label="Brand Presence" value={summary.brand_presence_rate} tone="sky" />
        <ScoreTile label="Official Citations" value={summary.official_citation_rate} tone="indigo" />
        <ScoreTile label="Ollama Match" value={summary.internal_external_alignment_score} tone="stone" />
      </div>

      <div className="mb-6 rounded-lg border border-stone-200 bg-stone-50 px-3 py-2 text-xs text-stone-600">
        {summary.questions_tested} questions tested across {summary.providers_tested} Ollama provider{summary.providers_tested === 1 ? '' : 's'}.
        {analysis.artifact_path ? ` Saved to ${analysis.artifact_path}.` : ''}
      </div>

      {analysis.questions.length > 0 && (
        <div className="rounded-lg border border-stone-200 bg-white px-4">
          {analysis.questions.map((question) => (
            <QuestionBlock key={question.prompt} question={question} />
          ))}
        </div>
      )}
    </div>
  );
}
