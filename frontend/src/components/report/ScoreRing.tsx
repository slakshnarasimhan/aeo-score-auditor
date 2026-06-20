'use client';

import { RadialBarChart, RadialBar, PolarAngleAxis } from 'recharts';
import { getBarColorHex } from '@/lib/report-utils';

interface ScoreRingProps {
  score: number;
  max?: number;
  size?: number;
  label?: string;
}

export function ScoreRing({ score, max = 100, size = 180, label }: ScoreRingProps) {
  const percentage = Math.min(100, (score / max) * 100);
  const color = getBarColorHex(percentage);
  const data = [{ value: percentage, fill: color }];

  return (
    <div className="relative flex flex-col items-center" style={{ width: size, height: size }}>
      <RadialBarChart
        width={size}
        height={size}
        cx={size / 2}
        cy={size / 2}
        innerRadius="72%"
        outerRadius="100%"
        barSize={12}
        data={data}
        startAngle={90}
        endAngle={-270}
      >
        <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
        <RadialBar
          background={{ fill: '#e7e5e4' }}
          dataKey="value"
          cornerRadius={8}
          isAnimationActive
        />
      </RadialBarChart>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-4xl font-bold text-stone-900">{Math.round(score)}</span>
        <span className="text-sm text-stone-500">/ {max}</span>
        {label && <span className="mt-1 text-xs font-medium text-stone-400 uppercase tracking-wider">{label}</span>}
      </div>
    </div>
  );
}
