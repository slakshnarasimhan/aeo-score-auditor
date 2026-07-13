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

const stageOrder = [
  'problem_recognition',
  'solution_discovery',
  'use_case_fit',
  'provider_comparison',
  'branded_validation',
  'implementation',
];

const stageDescriptions: Record<string, string> = {
  problem_recognition: 'The user describes a problem without knowing the category or brand.',
  solution_discovery: 'The user searches for a type of solution or provider.',
  use_case_fit: 'The user tests whether the solution can handle a concrete need.',
  provider_comparison: 'The user compares providers, approaches, or buying options.',
  branded_validation: 'The user already knows the brand and validates fit and proof.',
  implementation: 'The user asks about adoption, integration, support, or procurement.',
};

function inferStage(prompt: PromptGapResult, brand: string) {
  if (prompt.journey_stage) return prompt.journey_stage;
  const isBranded = prompt.prompt.toLowerCase().includes(brand.toLowerCase());
  if (isBranded) {
    return ['transactional', 'support'].includes(prompt.intent)
      ? 'implementation'
      : 'branded_validation';
  }
  if (prompt.intent === 'comparison') return 'provider_comparison';
  if (prompt.intent === 'feature') return 'use_case_fit';
  if (['transactional', 'support'].includes(prompt.intent)) return 'implementation';
  return 'solution_discovery';
}

function PromptRow({ prompt }: { prompt: PromptGapResult }) {
  const style = coverageStyles[prompt.coverage] ?? coverageStyles.missing;
  const evidenceItems = prompt.evidence.slice(0, 3);
  const eligibility = prompt.eligibility_score ?? prompt.answerability_score;
  const completeness = prompt.answer_completeness_score ?? prompt.answerability_score;
  const answer = prompt.answer ?? prompt.llm_evaluation?.answer;

  return (
    <div className="py-4 border-b border-stone-100 last:border-b-0">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-stone-900 leading-snug">
            {prompt.prompt}
          </p>
          <p className="mt-1 text-xs uppercase tracking-wider text-stone-400">
            {prompt.audience_scope ?? 'unbranded'} · {prompt.intent}
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-2 shrink-0">
          <span className="rounded border border-sky-200 bg-sky-50 px-2 py-1 text-xs font-semibold text-sky-800">
            Eligibility {eligibility}
          </span>
          <span className="rounded border border-indigo-200 bg-indigo-50 px-2 py-1 text-xs font-semibold text-indigo-800">
            Complete {completeness}
          </span>
          <span className={`rounded-full border px-2.5 py-1 text-xs font-bold capitalize ${style}`}>
            {prompt.coverage}
          </span>
        </div>
      </div>

      <p className="mt-2 text-sm text-stone-600">{prompt.gap}</p>
      {answer && (
        <p className="mt-2 rounded-md bg-indigo-50 px-3 py-2 text-sm text-indigo-900">
          {answer}
        </p>
      )}
      <p className="mt-1 text-sm text-indigo-700">{prompt.recommended_fix}</p>

      {evidenceItems.length > 0 && (
        <div className="mt-3 rounded-lg border border-stone-200 bg-stone-50 p-3">
          <p className="text-xs font-semibold uppercase tracking-wider text-stone-500">
            Website evidence
          </p>
          <div className="mt-2 space-y-2">
            {evidenceItems.map((evidence, index) => (
              <div key={`${evidence.url}-${index}`}>
                <p className="text-xs text-stone-700 leading-relaxed">
                  {evidence.text}
                </p>
                <p className="mt-1 truncate text-[11px] text-stone-400" title={evidence.url}>
                  {evidence.url}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function PromptGapChapter({ analysis }: PromptGapChapterProps) {
  const prompts = [...analysis.prompts].sort((a, b) => {
    const aStage = a.stage_rank ?? stageOrder.indexOf(inferStage(a, analysis.brand));
    const bStage = b.stage_rank ?? stageOrder.indexOf(inferStage(b, analysis.brand));
    return aStage - bStage || (a.question_rank ?? 99) - (b.question_rank ?? 99);
  });
  const groupedPrompts = stageOrder
    .map((stage) => ({
      stage,
      prompts: prompts.filter((prompt) => inferStage(prompt, analysis.brand) === stage),
    }))
    .filter((group) => group.prompts.length > 0);
  const counts = analysis.summary.coverage_counts;

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600 mb-2">
        Prompt Portfolio
      </p>
      <h2 className="font-display text-2xl md:text-3xl font-bold text-stone-900 mb-3">
        Demand-to-Answer Opportunities
      </h2>
      <p className="text-sm text-stone-600 leading-relaxed mb-6">
        These questions model how users move from an unbranded problem to evaluating and
        adopting {analysis.brand}. Eligibility measures whether an answer engine can infer
        the brand is relevant; completeness measures whether the website can support a useful answer.
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
            Deterministic website retrieval mode
            {analysis.llm_evaluation?.reason ? `: ${analysis.llm_evaluation.reason}` : '.'}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
        <div className="rounded-lg border border-sky-100 bg-sky-50 p-3">
          <p className="text-xs text-sky-700 font-semibold">AEO Eligibility</p>
          <p className="text-2xl font-bold text-sky-800 tabular-nums">
            {analysis.summary.eligibility_score ?? analysis.summary.coverage_score}%
          </p>
        </div>
        <div className="rounded-lg border border-indigo-100 bg-indigo-50 p-3">
          <p className="text-xs text-indigo-700 font-semibold">Answer Completeness</p>
          <p className="text-2xl font-bold text-indigo-800 tabular-nums">
            {analysis.summary.answer_completeness_score ?? analysis.summary.coverage_score}%
          </p>
        </div>
        <div className="rounded-lg border border-stone-200 bg-stone-50 p-3">
          <p className="text-xs text-stone-600 font-semibold">Coverage Gaps</p>
          <p className="text-2xl font-bold text-stone-800 tabular-nums">
            {(counts.partial ?? 0) + (counts.weak ?? 0) + (counts.missing ?? 0)}
          </p>
        </div>
      </div>

      <div className="space-y-6">
        {groupedPrompts.map(({ stage, prompts: stagePrompts }) => (
          <section key={stage}>
            <div className="mb-2 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h3 className="text-base font-bold text-stone-900">
                  {stagePrompts[0]?.journey_label ?? stage.replaceAll('_', ' ')}
                </h3>
                <p className="text-xs text-stone-500">{stageDescriptions[stage]}</p>
              </div>
              <span className="text-xs font-semibold text-stone-400">
                {stagePrompts.length} questions
              </span>
            </div>
            <div className="rounded-lg border border-stone-200 bg-white px-4">
              {stagePrompts.map((prompt) => (
                <PromptRow key={prompt.prompt} prompt={prompt} />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
