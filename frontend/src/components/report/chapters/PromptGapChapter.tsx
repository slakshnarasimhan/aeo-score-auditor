'use client';

import { PromptAnalysis, PromptGapResult } from '@/types/audit';

interface PromptGapChapterProps {
  analysis: PromptAnalysis;
}

const coverageStyles: Record<string, string> = {
  strong: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  partial: 'bg-amber-50 text-amber-700 border-amber-200',
  weak: 'bg-orange-50 text-orange-700 border-orange-200',
  missing: 'bg-rose-50 text-rose-700 border-rose-200',
};

function PromptRow({ prompt }: { prompt: PromptGapResult }) {
  const style = coverageStyles[prompt.coverage] ?? coverageStyles.missing;
  const evidence = prompt.evidence[0];

  return (
    <div className="py-4 border-b border-stone-100 last:border-b-0">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-stone-900 leading-snug">
            {prompt.prompt}
          </p>
          <p className="mt-1 text-xs uppercase tracking-wider text-stone-400">
            {prompt.intent}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`rounded-full border px-2.5 py-1 text-xs font-bold capitalize ${style}`}>
            {prompt.coverage}
          </span>
          <span className="text-sm font-bold tabular-nums text-stone-700">
            {prompt.answerability_score}
          </span>
        </div>
      </div>

      <p className="mt-2 text-sm text-stone-600">{prompt.gap}</p>
      {prompt.llm_evaluation?.answer && (
        <p className="mt-2 rounded-md bg-indigo-50 px-3 py-2 text-sm text-indigo-900">
          {prompt.llm_evaluation.answer}
        </p>
      )}
      <p className="mt-1 text-sm text-indigo-700">{prompt.recommended_fix}</p>

      {evidence && (
        <div className="mt-3 rounded-lg border border-stone-200 bg-stone-50 p-3">
          <p className="text-xs font-semibold uppercase tracking-wider text-stone-500">
            Best local evidence
          </p>
          <p className="mt-1 text-xs text-stone-700 leading-relaxed">
            {evidence.text}
          </p>
          <p className="mt-1 truncate text-[11px] text-stone-400" title={evidence.url}>
            {evidence.url}
          </p>
        </div>
      )}
    </div>
  );
}

export function PromptGapChapter({ analysis }: PromptGapChapterProps) {
  const prompts = [...analysis.prompts].sort(
    (a, b) => a.answerability_score - b.answerability_score
  );
  const priorityPrompts = prompts.filter((p) => p.coverage !== 'strong').slice(0, 8);
  const visiblePrompts = priorityPrompts.length > 0 ? priorityPrompts : prompts.slice(0, 8);
  const counts = analysis.summary.coverage_counts;

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600 mb-2">
        Prompt Portfolio
      </p>
      <h2 className="font-display text-2xl md:text-3xl font-bold text-stone-900 mb-3">
        Local Answerability Gaps
      </h2>
      <p className="text-sm text-stone-600 leading-relaxed mb-6">
        Simulated against crawled site content for {analysis.brand}. These prompts show
        whether the site has local evidence an AI answer engine could cite.
      </p>
      <div className="mb-6 rounded-lg border border-stone-200 bg-stone-50 px-3 py-2 text-xs text-stone-600">
        {analysis.evaluation_mode === 'llm' ? (
          <span>
            LLM evaluated with {analysis.llm_evaluation?.provider ?? 'provider'}{' '}
            {analysis.llm_evaluation?.model ? `(${analysis.llm_evaluation.model})` : ''}
            {analysis.llm_evaluation?.evaluated_prompts
              ? ` across ${analysis.llm_evaluation.evaluated_prompts} prompts`
              : ''}
            .
          </span>
        ) : (
          <span>
            Deterministic local retrieval mode
            {analysis.llm_evaluation?.reason ? `: ${analysis.llm_evaluation.reason}` : '.'}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
        <div className="rounded-lg border border-indigo-100 bg-indigo-50 p-3">
          <p className="text-xs text-indigo-700 font-semibold">Coverage</p>
          <p className="text-2xl font-bold text-indigo-800 tabular-nums">
            {analysis.summary.coverage_score}%
          </p>
        </div>
        {(['strong', 'partial', 'weak', 'missing'] as const).map((key) => (
          <div key={key} className={`rounded-lg border p-3 ${coverageStyles[key]}`}>
            <p className="text-xs font-semibold capitalize">{key}</p>
            <p className="text-2xl font-bold tabular-nums">{counts[key] ?? 0}</p>
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-stone-200 bg-white px-4">
        {visiblePrompts.map((prompt) => (
          <PromptRow key={prompt.prompt} prompt={prompt} />
        ))}
      </div>
    </div>
  );
}
