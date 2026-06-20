export function getCategoryColor(percentage: number): string {
  if (percentage >= 80) return 'text-emerald-600';
  if (percentage >= 60) return 'text-amber-600';
  if (percentage >= 40) return 'text-orange-600';
  return 'text-rose-600';
}

export function getBarColor(percentage: number): string {
  if (percentage >= 80) return 'bg-emerald-500';
  if (percentage >= 60) return 'bg-amber-500';
  if (percentage >= 40) return 'bg-orange-500';
  return 'bg-rose-500';
}

export function getBarColorHex(percentage: number): string {
  if (percentage >= 80) return '#10b981';
  if (percentage >= 60) return '#f59e0b';
  if (percentage >= 40) return '#f97316';
  return '#f43f5e';
}

export function getGradeColor(grade: string): string {
  if (grade.startsWith('A')) return 'text-emerald-600';
  if (grade.startsWith('B')) return 'text-amber-600';
  if (grade.startsWith('C')) return 'text-orange-600';
  return 'text-rose-600';
}

export function formatCategoryName(category: string): string {
  return category.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

export function getCategoryDescription(category: string): string {
  const descriptions: Record<string, string> = {
    answerability: 'How well the content directly answers questions',
    structured_data: 'Implementation of Schema.org and structured markup',
    authority: 'Author credentials, citations, and trust signals',
    content_quality: 'Depth, uniqueness, and freshness of content',
    citationability: 'Clarity of facts, data tables, and trustworthiness',
    technical: 'Page performance, mobile-friendliness, and SEO basics',
    ai_citation: 'Likelihood of being cited by AI models',
  };
  return descriptions[category] || '';
}

export function getScoreLabel(score: number): string {
  if (score >= 90) return 'Excellent';
  if (score >= 80) return 'Strong';
  if (score >= 70) return 'Good';
  if (score >= 60) return 'Fair';
  if (score >= 40) return 'Needs Work';
  return 'Critical';
}
