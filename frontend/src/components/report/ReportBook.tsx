'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Download } from 'lucide-react';
import { ReportChapter } from './ReportChapter';
import { ChapterNav } from './ChapterNav';
import { CoverChapter } from './chapters/CoverChapter';
import { SummaryChapter } from './chapters/SummaryChapter';
import { CategoryChapter } from './chapters/CategoryChapter';
import { GeoChapter } from './chapters/GeoChapter';
import { ActionsChapter } from './chapters/ActionsChapter';
import { AuditReportResult, isDomainResult } from '@/types/audit';
import { formatCategoryName } from '@/lib/report-utils';

type ChapterType = 'cover' | 'summary' | 'category' | 'geo' | 'actions';

interface ChapterDef {
  id: string;
  type: ChapterType;
  label: string;
  category?: string;
  categoryIndex?: number;
}

interface ReportBookProps {
  result: AuditReportResult;
  auditType: 'page' | 'domain';
  sourceUrl: string;
  detailedPDF: boolean;
  onDetailedPDFChange: (value: boolean) => void;
  onDownloadPDF: () => void;
}

function buildChapters(result: AuditReportResult): ChapterDef[] {
  const chapters: ChapterDef[] = [
    { id: 'cover', type: 'cover', label: 'Cover' },
    { id: 'summary', type: 'summary', label: 'Summary' },
  ];

  Object.keys(result.breakdown).forEach((category, i) => {
    chapters.push({
      id: `category-${category}`,
      type: 'category',
      label: formatCategoryName(category).split(' ')[0],
      category,
      categoryIndex: i + 1,
    });
  });

  if (isDomainResult(result) && result.geo_score) {
    chapters.push({ id: 'geo', type: 'geo', label: 'GEO' });
  }

  chapters.push({ id: 'actions', type: 'actions', label: 'Actions' });
  return chapters;
}

export function ReportBook({
  result,
  auditType,
  sourceUrl,
  detailedPDF,
  onDetailedPDFChange,
  onDownloadPDF,
}: ReportBookProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  const chapters = useMemo(() => buildChapters(result), [result]);

  const scrollToChapter = useCallback((index: number) => {
    const container = scrollRef.current;
    if (!container) return;
    const clamped = Math.max(0, Math.min(index, chapters.length - 1));
    container.scrollTo({
      left: clamped * container.clientWidth,
      behavior: 'smooth',
    });
    setActiveIndex(clamped);
  }, [chapters.length]);

  useEffect(() => {
    const container = scrollRef.current;
    if (!container) return;

    const handleScroll = () => {
      const index = Math.round(container.scrollLeft / container.clientWidth);
      setActiveIndex(Math.max(0, Math.min(index, chapters.length - 1)));
    };

    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => container.removeEventListener('scroll', handleScroll);
  }, [chapters.length]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') scrollToChapter(activeIndex - 1);
      if (e.key === 'ArrowRight') scrollToChapter(activeIndex + 1);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeIndex, scrollToChapter]);

  return (
    <section className="report-book w-full mt-8 -mx-4 md:-mx-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 px-4 md:px-8 mb-4">
        <div>
          <h2 className="font-display text-xl font-bold text-stone-800">Audit Report</h2>
          <p className="text-sm text-stone-500">
            Scroll horizontally or use arrow keys to browse chapters
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-stone-600 cursor-pointer">
            <input
              type="checkbox"
              checked={detailedPDF}
              onChange={(e) => onDetailedPDFChange(e.target.checked)}
              className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
            />
            <span>Detailed PDF</span>
          </label>
          <button
            onClick={onDownloadPDF}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-stone-800 text-white rounded-lg hover:bg-stone-700 transition-colors text-sm font-medium shadow-md"
          >
            <Download className="w-4 h-4" />
            Download PDF
          </button>
        </div>
      </div>

      <div className="report-book-viewport rounded-2xl overflow-hidden border border-stone-700/30 shadow-2xl">
        <div
          ref={scrollRef}
          className="report-book-scroll flex overflow-x-auto overflow-y-hidden snap-x snap-mandatory"
        >
          {chapters.map((chapter, index) => {
            let content;
            if (chapter.type === 'cover') {
              content = (
                <CoverChapter result={result} auditType={auditType} sourceUrl={sourceUrl} />
              );
            } else if (chapter.type === 'summary') {
              content = <SummaryChapter result={result} />;
            } else if (chapter.type === 'category' && chapter.category) {
              content = (
                <CategoryChapter
                  category={chapter.category}
                  data={result.breakdown[chapter.category]}
                  chapterIndex={chapter.categoryIndex ?? 1}
                />
              );
            } else if (chapter.type === 'geo' && isDomainResult(result) && result.geo_score) {
              content = <GeoChapter geoScore={result.geo_score} />;
            } else if (chapter.type === 'actions') {
              content = <ActionsChapter result={result} />;
            }

            return (
              <ReportChapter
                key={chapter.id}
                isActive={index === activeIndex}
                chapterNumber={index + 1}
                totalChapters={chapters.length}
              >
                {content}
              </ReportChapter>
            );
          })}
        </div>

        <ChapterNav
          labels={chapters.map((c) => c.label)}
          activeIndex={activeIndex}
          onSelect={scrollToChapter}
          onPrev={() => scrollToChapter(activeIndex - 1)}
          onNext={() => scrollToChapter(activeIndex + 1)}
          canPrev={activeIndex > 0}
          canNext={activeIndex < chapters.length - 1}
        />
      </div>
    </section>
  );
}
