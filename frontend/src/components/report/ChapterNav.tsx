'use client';

import { ChevronLeft, ChevronRight } from 'lucide-react';

interface ChapterNavProps {
  labels: string[];
  activeIndex: number;
  onSelect: (index: number) => void;
  onPrev: () => void;
  onNext: () => void;
  canPrev: boolean;
  canNext: boolean;
}

export function ChapterNav({
  labels,
  activeIndex,
  onSelect,
  onPrev,
  onNext,
  canPrev,
  canNext,
}: ChapterNavProps) {
  return (
    <div className="flex items-center justify-between gap-4 px-4 md:px-8 py-3 border-t border-stone-800/40 bg-stone-900/40 backdrop-blur-sm">
      <button
        onClick={onPrev}
        disabled={!canPrev}
        className="flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-medium text-stone-200 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        aria-label="Previous chapter"
      >
        <ChevronLeft className="w-4 h-4" />
        <span className="hidden sm:inline">Prev</span>
      </button>

      <div className="flex items-center gap-2 overflow-x-auto max-w-[60vw] scrollbar-thin py-1">
        {labels.map((label, i) => (
          <button
            key={i}
            onClick={() => onSelect(i)}
            className="group flex flex-col items-center gap-1 shrink-0"
            aria-label={`Go to ${label}`}
            aria-current={i === activeIndex ? 'true' : undefined}
          >
            <span
              className={`block w-2.5 h-2.5 rounded-full transition-all ${
                i === activeIndex
                  ? 'bg-indigo-400 scale-125 ring-2 ring-indigo-400/40'
                  : 'bg-stone-500 group-hover:bg-stone-300'
              }`}
            />
            <span
              className={`text-[10px] uppercase tracking-wider hidden md:block max-w-[72px] truncate ${
                i === activeIndex ? 'text-indigo-300 font-semibold' : 'text-stone-500'
              }`}
            >
              {label}
            </span>
          </button>
        ))}
      </div>

      <button
        onClick={onNext}
        disabled={!canNext}
        className="flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-medium text-stone-200 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        aria-label="Next chapter"
      >
        <span className="hidden sm:inline">Next</span>
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}
