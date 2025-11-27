"use client";

import { useState, useEffect } from 'react';

interface ScoreBreakdown {
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

interface AuditResult {
  overall_score: number;
  grade: string;
  breakdown: Record<string, ScoreBreakdown>;
}

interface DomainAuditResult {
  domain: string;
  overall_score: number;
  grade: string;
  pages_audited: number;
  pages_successful: number;
  breakdown: Record<string, ScoreBreakdown>;
  page_results?: Array<any>;
  best_page?: any;
  worst_page?: any;
}

interface ProgressUpdate {
  status: string;
  current_step: string;
  percentage: number;
  pages_audited: number;
  total_urls: number;
  message: string;
  current_url?: string;
}

export default function Home() {
  const [url, setUrl] = useState<string>('');
  const [domain, setDomain] = useState<string>('');
  const [maxPages, setMaxPages] = useState<number>(100);
  const [auditType, setAuditType] = useState<'page' | 'domain'>('page');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [auditResult, setAuditResult] = useState<AuditResult | null>(null);
  const [domainResult, setDomainResult] = useState<DomainAuditResult | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [detailViewCategory, setDetailViewCategory] = useState<string | null>(null);
  
  // Progress tracking
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const openDetailView = (category: string) => {
    setDetailViewCategory(category);
  };

  const closeDetailView = () => {
    setDetailViewCategory(null);
  };

  // SSE for progress tracking
  useEffect(() => {
    if (!jobId) return;

    const eventSource = new EventSource(`http://localhost:8000/api/v1/audit/domain/progress/${jobId}`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('SSE received:', data); // Debug log
        
        if (data.status === 'done' && data.result) {
          // Final result received
          console.log('Final result received:', data.result);
          setDomainResult(data.result);
          setProgress(null);
          setLoading(false);
          setJobId(null);
          eventSource.close();
        } else {
          // Progress update
          setProgress(data);
        }
      } catch (e) {
        console.error('Failed to parse SSE data:', e, 'Event data:', event.data);
      }
    };

    eventSource.onerror = () => {
      console.error('SSE connection error');
      eventSource.close();
      setLoading(false);
      setJobId(null);
    };

    return () => {
      eventSource.close();
    };
  }, [jobId]);

  const handlePageAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setAuditResult(null);
    setDomainResult(null);
    setProgress(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/audit/page', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url, deep_crawl: false, re_audit: false }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.result) {
        setAuditResult(data.result);
      } else {
        setError("Audit completed but no result data was returned.");
      }
    } catch (err: any) {
      setError(`Failed to audit page: ${err.message}`);
      console.error("Audit error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDomainAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setAuditResult(null);
    setDomainResult(null);
    setProgress(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/audit/domain', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          domain, 
          options: { max_pages: maxPages } 
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setJobId(data.job_id);
      setProgress({
        status: 'queued',
        current_step: 'Starting...',
        percentage: 0,
        pages_audited: 0,
        total_urls: maxPages,
        message: 'Initializing domain audit'
      });
    } catch (err: any) {
      setError(`Failed to start domain audit: ${err.message}`);
      console.error("Domain audit error:", err);
      setLoading(false);
    }
  };

  const getCategoryColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-yellow-600';
    if (percentage >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getBarColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 60) return 'bg-yellow-500';
    if (percentage >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getGradeColor = (grade: string) => {
    if (grade.startsWith('A')) return 'text-green-600';
    if (grade.startsWith('B')) return 'text-yellow-600';
    if (grade.startsWith('C')) return 'text-orange-600';
    return 'text-red-600';
  };

  const formatCategoryName = (category: string) => {
    return category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getCategoryDescription = (category: string) => {
    const descriptions: Record<string, string> = {
      answerability: "How well the content directly answers questions",
      structured_data: "Implementation of Schema.org and structured markup",
      authority: "Author credentials, citations, and trust signals",
      content_quality: "Depth, uniqueness, and freshness of content",
      citationability: "Clarity of facts, data tables, and trustworthiness",
      technical: "Page performance, mobile-friendliness, and SEO basics",
      ai_citation: "Likelihood of being cited by AI models"
    };
    return descriptions[category] || "";
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="w-full max-w-6xl bg-white shadow-2xl rounded-2xl p-8 mb-8">
        <h1 className="text-5xl font-bold mb-2 text-center text-gray-900">
          AEO Score Auditor
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Answer Engine Optimization Analysis Tool
        </p>

        {/* Audit Type Selector */}
        <div className="flex justify-center mb-6 space-x-4">
          <button
            onClick={() => setAuditType('page')}
            className={`px-6 py-2 rounded-lg font-medium transition-all ${
              auditType === 'page'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Single Page
          </button>
          <button
            onClick={() => setAuditType('domain')}
            className={`px-6 py-2 rounded-lg font-medium transition-all ${
              auditType === 'domain'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Entire Domain
          </button>
        </div>

        {/* Forms */}
        {auditType === 'page' ? (
          <form onSubmit={handlePageAudit} className="flex flex-col gap-4">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter page URL (e.g., https://example.com/article)"
              className="p-4 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              disabled={loading}
            />
            <button
              type="submit"
              className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 disabled:opacity-50 font-semibold shadow-lg"
              disabled={loading}
            >
              {loading ? '🔍 Auditing Page...' : '🚀 Audit Page'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleDomainAudit} className="flex flex-col gap-4">
            <input
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="Enter domain (e.g., example.com or https://example.com)"
              className="p-4 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              disabled={loading}
            />
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Pages (0 for unlimited)
                </label>
                <input
                  type="number"
                  value={maxPages}
                  onChange={(e) => setMaxPages(parseInt(e.target.value) || 0)}
                  min="0"
                  max="1000"
                  className="w-full p-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={loading}
                />
              </div>
            </div>
            <button
              type="submit"
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-4 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all duration-200 disabled:opacity-50 font-semibold shadow-lg"
              disabled={loading}
            >
              {loading ? '🌐 Crawling Domain...' : `🌐 Audit Domain ${maxPages > 0 ? `(up to ${maxPages} pages)` : '(unlimited)'}`}
            </button>
          </form>
        )}

        {/* Progress Bar */}
        {progress && (
          <div className="mt-6 p-6 bg-blue-50 border-2 border-blue-200 rounded-xl">
            <h3 className="text-xl font-semibold mb-4 text-blue-900">
              {progress.current_step}
            </h3>
            <div className="relative w-full bg-gray-200 rounded-full h-6 mb-3">
              <div
                className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress.percentage}%` }}
              >
                <span className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-white">
                  {progress.percentage.toFixed(1)}%
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-700">
              {progress.message}
            </p>
            {progress.pages_audited > 0 && (
              <p className="text-sm text-gray-600 mt-2">
                Audited: {progress.pages_audited}/{progress.total_urls} pages
              </p>
            )}
            {progress.current_url && (
              <p className="text-xs text-gray-500 mt-1 truncate">
                Current: {progress.current_url}
              </p>
            )}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded">
            <p className="font-bold">❌ Error:</p>
            <p>{error}</p>
          </div>
        )}

        {/* Single Page Results */}
        {auditResult && (
          <div className="mt-8 p-6 bg-gradient-to-br from-green-50 to-blue-50 border-2 border-green-200 rounded-xl">
            <h2 className="text-3xl font-bold mb-4 text-gray-800">📊 Audit Results</h2>
            <div className="flex items-baseline gap-4 mb-6">
              <span className="text-5xl font-extrabold text-gray-900">{auditResult.overall_score}</span>
              <span className="text-2xl text-gray-600">/100</span>
              <span className={`text-3xl font-bold ml-4 ${getGradeColor(auditResult.grade)}`}>
                Grade: {auditResult.grade}
              </span>
            </div>

            <h3 className="text-2xl font-semibold mb-4 text-gray-700">Score Breakdown:</h3>
            <div className="space-y-3">
              {Object.entries(auditResult.breakdown).map(([category, data]) => (
                <div key={category} className="bg-white p-4 rounded-lg shadow">
                  <button
                    onClick={() => toggleCategory(category)}
                    className="w-full text-left flex items-center justify-between hover:bg-gray-50 transition-colors rounded p-2"
                  >
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-lg">
                          {expandedCategories.has(category) ? '▼' : '▶'} {formatCategoryName(category)}
                        </span>
                        <span className={`font-bold text-lg ${getCategoryColor(data.percentage || 0)}`}>
                          {data.score}/{data.max} ({data.percentage?.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                          className={`h-3 rounded-full transition-all ${getBarColor(data.percentage || 0)}`}
                          style={{ width: `${data.percentage || 0}%` }}
                        />
                      </div>
                    </div>
                  </button>
                  
                  {/* Expandable Sub-scores */}
                  {expandedCategories.has(category) && data.sub_scores && (
                    <div className="mt-4 pl-6 border-l-2 border-gray-300 space-y-2">
                      <p className="text-sm text-gray-600 italic mb-3">{getCategoryDescription(category)}</p>
                      {Object.entries(data.sub_scores).map(([subCategory, score]) => (
                        <div key={subCategory} className="flex justify-between text-sm">
                          <span className="text-gray-600">
                            {formatCategoryName(subCategory)}
                          </span>
                          <span className="font-medium text-gray-800">{score}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Domain Results */}
        {domainResult && (
          <div className="mt-8 p-6 bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-200 rounded-xl">
            <h2 className="text-3xl font-bold mb-4 text-gray-800">🌐 Domain Audit Results</h2>
            
            <div className="mb-6 p-4 bg-white rounded-lg shadow">
              <p className="text-sm text-gray-600 mb-2">Domain: <span className="font-semibold">{domainResult.domain}</span></p>
              <p className="text-sm text-gray-600">
                Audited: <span className="font-semibold">{domainResult.pages_successful}/{domainResult.pages_audited}</span> pages successfully
              </p>
            </div>

            <div className="flex items-baseline gap-4 mb-6">
              <span className="text-5xl font-extrabold text-gray-900">{domainResult.overall_score}</span>
              <span className="text-2xl text-gray-600">/100</span>
              <span className={`text-3xl font-bold ml-4 ${getGradeColor(domainResult.grade)}`}>
                Grade: {domainResult.grade}
              </span>
            </div>

            <h3 className="text-2xl font-semibold mb-4 text-gray-700">Average Score Breakdown:</h3>
            <div className="space-y-3">
              {Object.entries(domainResult.breakdown).map(([category, data]) => (
                <div key={category} className="bg-white p-4 rounded-lg shadow">
                  <div className="flex items-center justify-between mb-2">
                    <button
                      onClick={() => toggleCategory(`domain_${category}`)}
                      className="flex-1 text-left hover:bg-gray-50 transition-colors rounded p-2"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-lg">
                          {expandedCategories.has(`domain_${category}`) ? '▼' : '▶'} {formatCategoryName(category)}
                        </span>
                        <span className={`font-bold text-lg ${getCategoryColor(data.percentage || 0)}`}>
                          {data.score}/{data.max} ({data.percentage?.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                          className={`h-3 rounded-full transition-all ${getBarColor(data.percentage || 0)}`}
                          style={{ width: `${data.percentage || 0}%` }}
                        />
                      </div>
                    </button>
                    <button
                      onClick={() => openDetailView(category)}
                      className="ml-4 px-4 py-2 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
                    >
                      Details
                    </button>
                  </div>
                  
                  {/* Quick summary when collapsed */}
                  {!expandedCategories.has(`domain_${category}`) && data.page_scores && (
                    <div className="text-xs text-gray-600 mt-2">
                      Best: {data.best_page?.score.toFixed(1)} | Worst: {data.worst_page?.score.toFixed(1)} | {data.page_scores.length} pages analyzed
                    </div>
                  )}
                  
                  {/* Expandable summary */}
                  {expandedCategories.has(`domain_${category}`) && (
                    <div className="mt-4 pl-6 border-l-2 border-gray-300">
                      <p className="text-sm text-gray-600 italic mb-3">{getCategoryDescription(category)}</p>
                      {data.best_page && data.worst_page && (
                        <div className="grid grid-cols-2 gap-3 mb-3">
                          <div className="bg-green-50 p-2 rounded">
                            <p className="text-xs font-semibold text-green-800">🏆 Best Score</p>
                            <p className="text-sm font-bold text-green-700">{data.best_page.score.toFixed(1)}/{data.max}</p>
                            <p className="text-xs text-gray-600 truncate">{data.best_page.url}</p>
                          </div>
                          <div className="bg-red-50 p-2 rounded">
                            <p className="text-xs font-semibold text-red-800">📉 Needs Work</p>
                            <p className="text-sm font-bold text-red-700">{data.worst_page.score.toFixed(1)}/{data.max}</p>
                            <p className="text-xs text-gray-600 truncate">{data.worst_page.url}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Best and Worst Pages */}
            {domainResult.best_page && domainResult.worst_page && (
              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                  <h4 className="font-semibold text-green-800 mb-2">🏆 Best Overall Page</h4>
                  <p className="text-xs text-gray-600 mb-1 truncate">{domainResult.best_page.url}</p>
                  <p className="text-2xl font-bold text-green-700">{domainResult.best_page.overall_score}/100</p>
                </div>
                <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                  <h4 className="font-semibold text-red-800 mb-2">📉 Needs Most Improvement</h4>
                  <p className="text-xs text-gray-600 mb-1 truncate">{domainResult.worst_page.url}</p>
                  <p className="text-2xl font-bold text-red-700">{domainResult.worst_page.overall_score}/100</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Detail View Modal */}
      {detailViewCategory && domainResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b p-6 flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">
                {formatCategoryName(detailViewCategory)} - Detailed Analysis
              </h2>
              <button
                onClick={closeDetailView}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>
            
            <div className="p-6">
              {domainResult.breakdown[detailViewCategory]?.page_scores && (
                <>
                  <p className="text-gray-600 mb-6">{getCategoryDescription(detailViewCategory)}</p>
                  
                  <div className="space-y-3">
                    {domainResult.breakdown[detailViewCategory].page_scores!
                      .sort((a, b) => b.score - a.score)
                      .map((page, index) => (
                        <div key={index} className="bg-gray-50 p-4 rounded-lg">
                          <div className="flex justify-between items-start mb-2">
                            <a 
                              href={page.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 hover:underline flex-1 mr-4"
                            >
                              {page.url}
                            </a>
                            <span className={`font-bold ${getCategoryColor(page.percentage)}`}>
                              {page.score.toFixed(1)}/{domainResult.breakdown[detailViewCategory].max}
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${getBarColor(page.percentage)}`}
                              style={{ width: `${page.percentage}%` }}
                            />
                          </div>
                          {page.sub_scores && Object.keys(page.sub_scores).length > 0 && (
                            <div className="mt-3 pl-4 border-l-2 border-gray-300 space-y-1">
                              {Object.entries(page.sub_scores).map(([sub, score]) => (
                                <div key={sub} className="flex justify-between text-xs">
                                  <span className="text-gray-600">{formatCategoryName(sub)}</span>
                                  <span className="font-medium">{score}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
