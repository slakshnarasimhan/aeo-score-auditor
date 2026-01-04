"use client";

import { useState, useEffect } from 'react';
import { API_URL } from '../config';

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

interface ContentClassification {
  type: string;
  confidence: string;
  profile_used: string;
  description: string;
}

interface AuditResult {
  overall_score: number;
  grade: string;
  breakdown: Record<string, ScoreBreakdown>;
  content_classification?: ContentClassification;
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
  content_classification?: ContentClassification;
}

interface ProgressUpdate {
  status: string;
  current_step: string;
  percentage: number;
  pages_audited: number;
  total_urls: number;
  urls_discovered: number;
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
  const [detailedPDF, setDetailedPDF] = useState<boolean>(false);
  
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

    const eventSource = new EventSource(`${API_URL}/api/v1/audit/domain/progress/${jobId}`);
    let completionTimeout: NodeJS.Timeout;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('SSE received:', data); // Debug log
        console.log('Progress values:', {
          status: data.status,
          percentage: data.percentage,
          pages_audited: data.pages_audited,
          total_urls: data.total_urls,
          urls_discovered: data.urls_discovered
        });
        
        if (data.status === 'done' && data.result) {
          // Final result received via SSE
          console.log('Final result received via SSE:', data.result);
          setDomainResult(data.result);
          setProgress(null);
          setLoading(false);
          setJobId(null);
          eventSource.close();
          if (completionTimeout) clearTimeout(completionTimeout);
        } else if (data.status === 'completed' && data.percentage === 100) {
          // Progress shows completed, wait for result or fetch it
          console.log('Audit completed at 100%, waiting for result...');
          console.log('Setting progress to:', data);
          setProgress(data);
          
          // Fallback: If result doesn't arrive via SSE in 2 seconds, fetch it directly
          completionTimeout = setTimeout(async () => {
            console.log('Result not received via SSE, fetching directly...');
            try {
              // Fetch the completed result directly
              const response = await fetch(`${API_URL}/api/v1/audit/domain/result/${jobId}`);
              if (response.ok) {
                const resultData = await response.json();
                console.log('Result fetched directly:', resultData);
                setDomainResult(resultData.result);
                setProgress(null);
                setLoading(false);
                setJobId(null);
                eventSource.close();
              }
            } catch (err) {
              console.error('Failed to fetch result:', err);
              setError('Audit completed but failed to fetch results. Please try again.');
              setProgress(null);
              setLoading(false);
              setJobId(null);
              eventSource.close();
            }
          }, 2000);
        } else {
          // Progress update
          console.log('Regular progress update, setting progress to:', data);
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
      if (completionTimeout) clearTimeout(completionTimeout);
    };

    return () => {
      eventSource.close();
      if (completionTimeout) clearTimeout(completionTimeout);
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
      const response = await fetch(`${API_URL}/api/v1/audit/page`, {
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
      const response = await fetch(`${API_URL}/api/v1/audit/domain`, {
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
        status: 'discovering',
        current_step: 'Starting discovery...',
        percentage: 0,
        pages_audited: 0,
        urls_discovered: 0,
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

  const extractDomainName = (url: string): string => {
    try {
      const urlObj = new URL(url);
      let hostname = urlObj.hostname;
      
      // Remove 'www.' prefix
      hostname = hostname.replace(/^www\./, '');
      
      // Extract the main domain name (e.g., 'aprisio' from 'aprisio.com')
      const parts = hostname.split('.');
      if (parts.length >= 2) {
        // For domain.tld, return 'domain'
        // For subdomain.domain.tld, return 'domain'
        return parts[parts.length - 2];
      }
      
      return hostname;
    } catch (e) {
      // Fallback if URL parsing fails
      return 'report';
    }
  };

  const downloadPDF = async (result: AuditResult | DomainAuditResult, type: 'page' | 'domain') => {
    try {
      const response = await fetch(`${API_URL}/api/v1/audit/pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          audit_result: result,
          audit_type: type,
          detailed: detailedPDF
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate PDF');
      }

      // Extract domain name from the audited URL or domain
      let auditedUrl: string;
      if (type === 'page') {
        // For single page audits, use the URL from state
        auditedUrl = url;
      } else {
        // For domain audits, use the domain field
        auditedUrl = (result as DomainAuditResult).domain;
      }
      
      const domainName = extractDomainName(auditedUrl);
      const filename = `aeo-report-${domainName}.pdf`;

      // Create blob and download
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);
    } catch (err: any) {
      setError(`Failed to download PDF: ${err.message}`);
      console.error('PDF download error:', err);
    }
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
        <p className="text-center text-gray-600 mb-2">
          Answer Engine Optimization Analysis Tool
        </p>
        <div className="text-center mb-8">
          <a 
            href="/scoring-guide.html" 
            target="_blank"
            className="text-blue-600 hover:text-blue-800 underline text-sm"
          >
            📊 View Complete Scoring Framework & Formulas →
          </a>
        </div>

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
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter page URL or local file path (e.g., https://example.com or file:///path/to/file.html)"
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
          <div className="mt-6 p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-300 rounded-xl shadow-lg">
            {/* Status Badge */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  progress.status === 'discovering' ? 'bg-yellow-200 text-yellow-800' :
                  progress.status === 'auditing' ? 'bg-blue-200 text-blue-800' :
                  progress.status === 'completed' ? 'bg-green-200 text-green-800' :
                  'bg-red-200 text-red-800'
                }`}>
                  {progress.status === 'discovering' ? '🔍 Discovering' :
                   progress.status === 'auditing' ? '⚡ Auditing' :
                   progress.status === 'completed' ? '✅ Completed' :
                   '❌ Failed'}
                </div>
                <h3 className="text-xl font-semibold text-gray-800">
                  {progress.current_step}
                </h3>
              </div>
              <span className="text-2xl font-bold text-blue-600">
                {progress.percentage.toFixed(0)}%
              </span>
            </div>

            {/* Progress Bar */}
            <div className="relative w-full bg-gray-200 rounded-full h-8 mb-4 shadow-inner">
              <div
                className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-full transition-all duration-500 ease-out shadow-md"
                style={{ width: `${progress.percentage}%` }}
              >
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-sm font-bold text-white drop-shadow">
                    {progress.percentage >= 10 ? `${progress.percentage.toFixed(1)}%` : ''}
                  </span>
                </div>
              </div>
            </div>

            {/* Detailed Info Grid */}
            <div className="grid grid-cols-2 gap-4 mb-3">
              {progress.urls_discovered > 0 && (
                <div className="bg-white rounded-lg p-3 shadow">
                  <p className="text-xs text-gray-500 mb-1">URLs Discovered</p>
                  <p className="text-2xl font-bold text-indigo-600">{progress.urls_discovered}</p>
                </div>
              )}
              {progress.total_urls > 0 && (
                <div className="bg-white rounded-lg p-3 shadow">
                  <p className="text-xs text-gray-500 mb-1">Progress</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {progress.pages_audited}/{progress.total_urls}
                  </p>
                </div>
              )}
            </div>

            {/* Message */}
            <div className="bg-white rounded-lg p-3 mb-2 shadow">
              <p className="text-sm font-medium text-gray-700">
                {progress.message}
              </p>
            </div>

            {/* Current URL */}
            {progress.current_url && (
              <div className="bg-indigo-50 rounded-lg p-3 border border-indigo-200">
                <p className="text-xs text-indigo-600 font-semibold mb-1">Currently Auditing:</p>
                <p className="text-xs text-gray-700 truncate">{progress.current_url}</p>
              </div>
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
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-3xl font-bold text-gray-800">📊 Audit Results</h2>
              <div className="flex flex-col items-end gap-2">
                <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={detailedPDF}
                    onChange={(e) => setDetailedPDF(e.target.checked)}
                    className="w-4 h-4 text-red-600 rounded focus:ring-red-500"
                  />
                  <span>Detailed PDF (includes all subsections)</span>
                </label>
                <button
                  onClick={() => downloadPDF(auditResult, 'page')}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2 shadow-lg"
                >
                  <span>📥</span>
                  <span>Download PDF</span>
                </button>
              </div>
            </div>
            {/* Content Type Badge */}
            {auditResult.content_classification && (
              <div className="mb-4 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-semibold text-indigo-900">Content Type:</span>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                    auditResult.content_classification.type === 'experiential' ? 'bg-purple-200 text-purple-800' :
                    auditResult.content_classification.type === 'informational' ? 'bg-blue-200 text-blue-800' :
                    auditResult.content_classification.type === 'transactional' ? 'bg-green-200 text-green-800' :
                    'bg-gray-200 text-gray-800'
                  }`}>
                    {auditResult.content_classification.type}
                  </span>
                  <span className="text-xs text-gray-600">
                    ({auditResult.content_classification.confidence} confidence)
                  </span>
                </div>
                <p className="text-xs text-gray-600 italic">{auditResult.content_classification.description}</p>
              </div>
            )}

            <div className="flex items-baseline gap-4 mb-6">
              <span className="text-5xl font-extrabold text-gray-900">{auditResult.overall_score}</span>
              <span className="text-2xl text-gray-600">/100</span>
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
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-3xl font-bold text-gray-800">🌐 Domain Audit Results</h2>
              <div className="flex flex-col items-end gap-2">
                <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={detailedPDF}
                    onChange={(e) => setDetailedPDF(e.target.checked)}
                    className="w-4 h-4 text-red-600 rounded focus:ring-red-500"
                  />
                  <span>Detailed PDF (includes all pages)</span>
                </label>
                <button
                  onClick={() => downloadPDF(domainResult, 'domain')}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2 shadow-lg"
                >
                  <span>📥</span>
                  <span>Download PDF</span>
                </button>
              </div>
            </div>
            
            <div className="mb-6 p-4 bg-white rounded-lg shadow">
              <p className="text-sm text-gray-600 mb-2">Domain: <span className="font-semibold">{domainResult.domain}</span></p>
              <p className="text-sm text-gray-600">
                Audited: <span className="font-semibold">{domainResult.pages_successful}/{domainResult.pages_audited}</span> pages successfully
              </p>
            </div>

            <div className="flex items-baseline gap-4 mb-6">
              <span className="text-5xl font-extrabold text-gray-900">{domainResult.overall_score}</span>
              <span className="text-2xl text-gray-600">/100</span>
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
