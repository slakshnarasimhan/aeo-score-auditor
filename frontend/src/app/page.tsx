"use client";

import { useState } from 'react';

interface ScoreBreakdown {
  score: number;
  max: number;
  percentage?: number;
  sub_scores?: Record<string, number>;
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

export default function Home() {
  const [url, setUrl] = useState<string>('');
  const [domain, setDomain] = useState<string>('');
  const [auditType, setAuditType] = useState<'page' | 'domain'>('page');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [auditResult, setAuditResult] = useState<AuditResult | null>(null);
  const [domainResult, setDomainResult] = useState<DomainAuditResult | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const handlePageAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setAuditResult(null);
    setDomainResult(null);

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

    try {
      const response = await fetch('http://localhost:8000/api/v1/audit/domain', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          domain, 
          options: { max_pages: 10 } 
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.result) {
        setDomainResult(data.result);
      } else {
        setError("Domain audit completed but no result data was returned.");
      }
    } catch (err: any) {
      setError(`Failed to audit domain: ${err.message}`);
      console.error("Domain audit error:", err);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-yellow-600';
    if (percentage >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getGradeColor = (grade: string) => {
    if (grade.startsWith('A')) return 'text-green-600';
    if (grade.startsWith('B')) return 'text-yellow-600';
    if (grade.startsWith('C')) return 'text-orange-600';
    return 'text-red-600';
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="w-full max-w-5xl bg-white shadow-2xl rounded-2xl p-8 mb-8">
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
            />
            <button
              type="submit"
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-4 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all duration-200 disabled:opacity-50 font-semibold shadow-lg"
              disabled={loading}
            >
              {loading ? '🌐 Crawling Domain...' : '🌐 Audit Entire Domain (up to 10 pages)'}
            </button>
          </form>
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
                        <span className="font-semibold capitalize text-lg">
                          {expandedCategories.has(category) ? '▼' : '▶'} {category.replace(/_/g, ' ')}
                        </span>
                        <span className={`font-bold text-lg ${getCategoryColor(data.percentage || 0)}`}>
                          {data.score}/{data.max} ({data.percentage?.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                          className={`h-3 rounded-full transition-all ${
                            (data.percentage || 0) >= 80 ? 'bg-green-500' :
                            (data.percentage || 0) >= 60 ? 'bg-yellow-500' :
                            (data.percentage || 0) >= 40 ? 'bg-orange-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${data.percentage || 0}%` }}
                        />
                      </div>
                    </div>
                  </button>
                  
                  {/* Expandable Sub-scores */}
                  {expandedCategories.has(category) && data.sub_scores && (
                    <div className="mt-4 pl-6 border-l-2 border-gray-300 space-y-2">
                      {Object.entries(data.sub_scores).map(([subCategory, score]) => (
                        <div key={subCategory} className="flex justify-between text-sm">
                          <span className="text-gray-600 capitalize">
                            {subCategory.replace(/_/g, ' ')}
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
                  <button
                    onClick={() => toggleCategory(`domain_${category}`)}
                    className="w-full text-left flex items-center justify-between hover:bg-gray-50 transition-colors rounded p-2"
                  >
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold capitalize text-lg">
                          {expandedCategories.has(`domain_${category}`) ? '▼' : '▶'} {category.replace(/_/g, ' ')}
                        </span>
                        <span className={`font-bold text-lg ${getCategoryColor(data.percentage || 0)}`}>
                          {data.score}/{data.max} ({data.percentage?.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                          className={`h-3 rounded-full transition-all ${
                            (data.percentage || 0) >= 80 ? 'bg-green-500' :
                            (data.percentage || 0) >= 60 ? 'bg-yellow-500' :
                            (data.percentage || 0) >= 40 ? 'bg-orange-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${data.percentage || 0}%` }}
                        />
                      </div>
                    </div>
                  </button>
                </div>
              ))}
            </div>

            {/* Best and Worst Pages */}
            {domainResult.best_page && domainResult.worst_page && (
              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                  <h4 className="font-semibold text-green-800 mb-2">🏆 Best Page</h4>
                  <p className="text-xs text-gray-600 mb-1 truncate">{domainResult.best_page.url}</p>
                  <p className="text-2xl font-bold text-green-700">{domainResult.best_page.overall_score}/100</p>
                </div>
                <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                  <h4 className="font-semibold text-red-800 mb-2">📉 Needs Improvement</h4>
                  <p className="text-xs text-gray-600 mb-1 truncate">{domainResult.worst_page.url}</p>
                  <p className="text-2xl font-bold text-red-700">{domainResult.worst_page.overall_score}/100</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
