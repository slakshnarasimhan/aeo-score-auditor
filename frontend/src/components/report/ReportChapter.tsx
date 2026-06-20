'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface ReportChapterProps {
  children: ReactNode;
  isActive: boolean;
  chapterNumber: number;
  totalChapters: number;
}

export function ReportChapter({ children, isActive, chapterNumber, totalChapters }: ReportChapterProps) {
  return (
    <div className="snap-start snap-always shrink-0 w-full min-w-full flex items-stretch justify-center px-4 md:px-8 py-6">
      <motion.article
        initial={false}
        animate={{
          opacity: isActive ? 1 : 0.55,
          scale: isActive ? 1 : 0.97,
        }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="report-page relative flex flex-col w-full max-w-3xl min-h-[520px] max-h-[72vh] overflow-hidden"
      >
        <div className="absolute top-4 right-6 text-xs text-stone-400 font-medium tracking-wide">
          {chapterNumber} / {totalChapters}
        </div>
        <div className="flex-1 overflow-y-auto p-8 md:p-10 pt-12">
          {children}
        </div>
      </motion.article>
    </div>
  );
}
