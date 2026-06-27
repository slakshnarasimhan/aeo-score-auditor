export interface ScoreBreakdown {
  score: number;
  max: number;
  percentage?: number;
  sub_scores?: Record<string, number>;
  applicability?: string;
  applicability_reason?: string;
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

export interface AuditProfile {
  type: string;
  label: string;
  confidence: string;
  description: string;
  reason?: string;
  extraction_goals: string[];
  recommended_schema: string[];
  not_applicable: string[];
}

export interface Recommendation {
  category: string;
  title: string;
  current_score?: number;
  max_score?: number;
  percentage?: number;
  priority?: number;
  impact?: string;
  applicability?: string;
  reason?: string;
  tips: string[];
}

export interface PromptEvidence {
  url: string;
  text: string;
  type: string;
  score: number;
  matched_terms: string[];
}

export interface PromptGapResult {
  prompt: string;
  intent: string;
  journey_stage?: string;
  journey_label?: string;
  stage_rank?: number;
  question_rank?: number;
  audience_scope?: 'unbranded' | 'branded';
  source?: string;
  market_scope?: string;
  win_likelihood?: string;
  coverage: 'strong' | 'partial' | 'weak' | 'missing';
  answerability_score: number;
  eligibility_score?: number;
  answer_completeness_score?: number;
  opportunity_score?: number;
  evidence: PromptEvidence[];
  gap: string;
  recommended_fix: string;
  deterministic_coverage?: string;
  deterministic_answerability_score?: number;
  llm_evaluation?: {
    available: boolean;
    coverage?: 'strong' | 'partial' | 'weak' | 'missing';
    answerability_score?: number;
    answer?: string;
    reasoning?: string;
    gaps?: string[];
    recommended_fix?: string;
    evidence_used?: Array<number | string>;
    error?: string;
  };
}

export interface PromptAnalysis {
  brand: string;
  topic: string;
  profile: string;
  evaluation_mode?: 'deterministic' | 'llm';
  llm_evaluation?: {
    enabled: boolean;
    provider?: string;
    model?: string;
    evaluated_prompts?: number;
    reason?: string;
  };
  summary: {
    total_prompts: number;
    coverage_score: number;
    eligibility_score?: number;
    answer_completeness_score?: number;
    coverage_counts: Record<string, number>;
    intent_counts: Record<string, Record<string, number>>;
    stage_counts?: Record<string, {
      label: string;
      total: number;
      eligibility_score: number;
      completeness_score: number;
    }>;
  };
  prompts: PromptGapResult[];
}

export interface ExternalAEOProviderResult {
  provider: string;
  model: string;
  available: boolean;
  error?: string;
  answer: string;
  citations: Array<{ url: string; title?: string }>;
  visibility_score: number;
  brand_mentioned: boolean;
  official_site_cited: boolean;
  citation_count?: number;
}

export interface ExternalAEOQuestionResult {
  prompt: string;
  journey_stage?: string;
  journey_label?: string;
  intent?: string;
  internal_eligibility_score: number;
  internal_answer_completeness_score: number;
  external_visibility_score: number;
  brand_presence_rate: number;
  official_citation_rate: number;
  internal_external_alignment_score: number;
  providers: ExternalAEOProviderResult[];
}

export interface ExternalAEOAnalysis {
  enabled: boolean;
  available: boolean;
  reason?: string;
  validated_at?: string;
  domain?: string;
  brand?: string;
  site_url?: string;
  artifact_path?: string;
  providers: Array<{
    name: string;
    label?: string;
    model?: string;
    available: boolean;
  }>;
  summary: {
    questions_tested: number;
    providers_tested: number;
    external_visibility_score: number;
    brand_presence_rate: number;
    official_citation_rate: number;
    internal_external_alignment_score: number;
    stage_counts: Record<string, {
      total: number;
      external_visibility_score: number;
      brand_presence_rate: number;
    }>;
  };
  questions: ExternalAEOQuestionResult[];
}

export interface PositioningAnalysis {
  brand: string;
  business_type: string;
  context_source?: string;
  market_scope: string;
  locations: string[];
  products: string[];
  value_props: string[];
  service_props: string[];
  usp_claims: string[];
  likely_wedge: string;
  constraints: string[];
  evidence_strength: 'strong' | 'partial' | 'weak' | 'missing';
  evidence: Array<{ url: string; text: string }>;
  recommended_proof: string[];
}

export interface AuditResult {
  overall_score: number;
  grade: string;
  breakdown: Record<string, ScoreBreakdown>;
  content_classification?: ContentClassification;
  audit_profile?: AuditProfile;
  extraction_goals?: string[];
  not_applicable?: string[];
  recommendations?: Recommendation[];
  positioning_analysis?: PositioningAnalysis;
  prompt_analysis?: PromptAnalysis;
  external_aeo_analysis?: ExternalAEOAnalysis;
  crawl_artifact_path?: string;
  crawl_source?: 'network' | 'local';
}

export interface DomainAuditResult {
  domain: string;
  domain_intelligence?: Record<string, unknown>;
  domain_strategy?: Record<string, unknown>;
  overall_score: number;
  grade: string;
  pages_audited: number;
  pages_successful: number;
  breakdown: Record<string, ScoreBreakdown>;
  page_results?: Array<unknown>;
  best_page?: { url: string; overall_score: number };
  worst_page?: { url: string; overall_score: number };
  content_classification?: ContentClassification;
  audit_profile?: AuditProfile;
  audit_profile_distribution?: Record<string, number>;
  content_type_distribution?: Record<string, number>;
  extraction_goals?: string[];
  not_applicable?: string[];
  recommendations?: Recommendation[];
  positioning_analysis?: PositioningAnalysis;
  prompt_analysis?: PromptAnalysis;
  external_aeo_analysis?: ExternalAEOAnalysis;
  geo_score?: GEOScore;
  crawl_artifact_path?: string;
  crawl_source?: 'network' | 'local';
}

export type AuditReportResult = AuditResult | DomainAuditResult;

export function isDomainResult(result: AuditReportResult): result is DomainAuditResult {
  return 'domain' in result;
}
