'use client';

import { PositioningAnalysis } from '@/types/audit';

interface PositioningChapterProps {
  analysis: PositioningAnalysis;
}

const strengthStyles: Record<string, string> = {
  strong: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  partial: 'bg-amber-50 text-amber-700 border-amber-200',
  weak: 'bg-orange-50 text-orange-700 border-orange-200',
  missing: 'bg-rose-50 text-rose-700 border-rose-200',
};

function ChipList({ items }: { items: string[] }) {
  if (!items?.length) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {items.slice(0, 8).map((item) => (
        <span key={item} className="rounded-md border border-stone-200 bg-stone-50 px-2.5 py-1 text-xs font-medium text-stone-700">
          {item}
        </span>
      ))}
    </div>
  );
}

export function PositioningChapter({ analysis }: PositioningChapterProps) {
  const strengthStyle = strengthStyles[analysis.evidence_strength] ?? strengthStyles.missing;

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600 mb-2">
        Positioning
      </p>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between mb-4">
        <h2 className="font-display text-2xl md:text-3xl font-bold text-stone-900">
          USP & Realistic Wedge
        </h2>
        <span className={`rounded-full border px-3 py-1 text-xs font-bold capitalize ${strengthStyle}`}>
          {analysis.evidence_strength} proof
        </span>
      </div>

      <div className="rounded-lg border border-indigo-100 bg-indigo-50 p-4 mb-6">
        <p className="text-xs font-semibold uppercase tracking-wider text-indigo-700 mb-1">
          Likely Wedge
        </p>
        <p className="text-sm font-semibold text-indigo-950 leading-relaxed">
          {analysis.likely_wedge}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-6">
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-stone-500">
            USP Signals
          </h3>
          <ul className="space-y-2">
            {analysis.usp_claims.slice(0, 5).map((claim) => (
              <li key={claim} className="text-sm text-stone-700 leading-relaxed">
                {claim}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-stone-500">
            Scope Constraints
          </h3>
          <ul className="space-y-2">
            {analysis.constraints.slice(0, 4).map((constraint) => (
              <li key={constraint} className="text-sm text-stone-700 leading-relaxed">
                {constraint}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mb-6 space-y-3">
        <ChipList items={[...analysis.locations, ...analysis.products, ...analysis.value_props]} />
      </div>

      {analysis.evidence[0] && (
        <div className="rounded-lg border border-stone-200 bg-white p-4 mb-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-stone-500">
            Best proof found
          </p>
          <p className="mt-2 text-sm text-stone-700 leading-relaxed">
            {analysis.evidence[0].text}
          </p>
          <p className="mt-1 truncate text-[11px] text-stone-400" title={analysis.evidence[0].url}>
            {analysis.evidence[0].url}
          </p>
        </div>
      )}

      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-stone-500">
        Proof To Add
      </h3>
      <ul className="space-y-2">
        {analysis.recommended_proof.slice(0, 4).map((item) => (
          <li key={item} className="text-sm text-stone-700 leading-relaxed">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
