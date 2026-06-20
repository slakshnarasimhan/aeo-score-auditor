export interface ScoreBreakdown {
  score: number;
  max: number;
  percentage?: number;
  sub_scores?: Record<string, number>;
  page_scores?: Array<{
    url: string;
    score: number;
    percentage: number;
    sub_scores?: Record<string, number>;
  }>;
  best_page?: {
    url: string;
    score: number;
  };
  worst_page?: {
    url: string;
    score: number;
  };
}

export interface GEOScore {
  geo_score: number;
  components: {
    brand_foundation: { score: number; max: number; evidence: string[] };
    topic_coverage: { score: number; max: number; evidence: string[] };
    consistency: { score: number; max: number; evidence: string[] };
    ai_recall: { score: number; max: number; evidence: string[] };
    trust: { score: number; max: number; evidence: string[] };
  };
  summary: string;
  recommended_actions: string[];
  brand_name: string;
  pages_analyzed: number;
}

export interface ContentClassification {
  type: string;
  confidence: string;
  profile_used: string;
  description: string;
}

export interface AuditResult {
  overall_score: number;
  grade: string;
  breakdown: Record<string, ScoreBreakdown>;
  content_classification?: ContentClassification;
}

export interface DomainAuditResult {
  domain: string;
  overall_score: number;
  grade: string;
  pages_audited: number;
  pages_successful: number;
  breakdown: Record<string, ScoreBreakdown>;
  page_results?: Array<unknown>;
  best_page?: { url: string; overall_score: number };
  worst_page?: { url: string; overall_score: number };
  content_classification?: ContentClassification;
  geo_score?: GEOScore;
}

export type AuditReportResult = AuditResult | DomainAuditResult;

export function isDomainResult(result: AuditReportResult): result is DomainAuditResult {
  return 'domain' in result;
}
