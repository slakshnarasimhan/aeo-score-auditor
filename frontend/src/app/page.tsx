"use client";

import { useState, useEffect } from 'react';
import { API_URL } from '../config';
import { ReportBook } from '@/components/report/ReportBook';
import { AuditResult, DomainAuditResult } from '@/types/audit';

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

const PROFILE_OPTIONS = [
  { value: 'auto', label: 'Auto-detect' },
  { value: 'ecommerce', label: 'Ecommerce' },
  { value: 'saas_app', label: 'SaaS / App' },
  { value: 'publisher', label: 'Publisher / Blog' },
  { value: 'local_business', label: 'Local Business' },
  { value: 'education', label: 'Education / Course' },
  { value: 'documentation', label: 'Documentation' },
  { value: 'general', label: 'General Website' },
];

function ProfileSelector({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
}) {
  return (
    <div className="mb-6 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <label htmlFor="site-profile" className="block text-sm font-semibold text-gray-800">
            Website Profile
          </label>
          <p className="mt-1 text-xs text-gray-500">
            Choose the extraction lens for recommendations, or let the auditor infer it.
          </p>
        </div>
        <select
          id="site-profile"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-lg border-2 border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-800 shadow-sm focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500 sm:w-64"
          disabled={disabled}
        >
          {PROFILE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

export default function Home() {
  const [url, setUrl] = useState<string>('');
  const [domain, setDomain] = useState<string>('');
  const [maxPages, setMaxPages] = useState<number>(100);
  const [siteProfile, setSiteProfile] = useState<string>('auto');
  const [llmPromptEval, setLlmPromptEval] = useState<boolean>(false);
  const [auditType, setAuditType] = useState<'page' | 'domain'>('page');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [auditResult, setAuditResult] = useState<AuditResult | null>(null);
  const [domainResult, setDomainResult] = useState<DomainAuditResult | null>(null);
  const [detailedPDF, setDetailedPDF] = useState<boolean>(false);
  
  // Progress tracking
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  // SSE for progress tracking
  useEffect(() => {
    if (!jobId) return;

    const eventSource = new EventSource(`${API_URL}/api/v1/audit/domain/progress/${jobId}`);
    let completionTimeout: ReturnType<typeof setTimeout> | undefined;
    let pollInterval: ReturnType<typeof setInterval> | undefined;

    const stopTracking = () => {
      eventSource.close();
      if (completionTimeout) clearTimeout(completionTimeout);
      if (pollInterval) clearInterval(pollInterval);
    };

    const finishWithResult = (result: DomainAuditResult) => {
      setDomainResult(result);
      setProgress(null);
      setLoading(false);
      setJobId(null);
      stopTracking();
    };

    const handleProgressData = (data: any) => {
      console.log('Progress received:', data);

      if (data.status === 'done' && data.result) {
        finishWithResult(data.result);
        return;
      }

      setProgress(data);

      if (data.status === 'failed') {
        setError(data.message || 'Domain audit failed.');
        setLoading(false);
        setJobId(null);
        stopTracking();
        return;
      }

      if (data.status === 'completed' && data.result) {
        finishWithResult(data.result);
        return;
      }

      if (data.status === 'completed') {
        if (completionTimeout) clearTimeout(completionTimeout);
        completionTimeout = setTimeout(async () => {
          try {
            const response = await fetch(`${API_URL}/api/v1/audit/domain/result/${jobId}`);
            if (response.ok) {
              const resultData = await response.json();
              finishWithResult(resultData.result);
            }
          } catch (err) {
            console.error('Failed to fetch completed result:', err);
          }
        }, 1000);
      }
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleProgressData(data);
      } catch (e) {
        console.error('Failed to parse SSE data:', e, 'Event data:', event.data);
      }
    };

    eventSource.onerror = () => {
      console.error('SSE connection error; continuing with polling fallback');
      eventSource.close();
    };

    pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/api/v1/audit/domain/status/${jobId}`);
        if (response.ok) {
          const data = await response.json();
          handleProgressData(data);
        }
      } catch (err) {
        console.error('Failed to poll domain audit status:', err);
      }
    }, 1500);

    return () => {
      stopTracking();
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
        body: JSON.stringify({
          url,
          deep_crawl: false,
          re_audit: false,
          options: { site_profile: siteProfile, llm_prompt_eval: llmPromptEval },
        }),
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
          options: {
            max_pages: maxPages,
            site_profile: siteProfile,
            llm_prompt_eval: llmPromptEval,
          } 
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

  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="w-full max-w-6xl bg-white shadow-2xl rounded-2xl p-8 mb-8">
        <h1 className="text-5xl font-bold mb-2 text-center text-gray-900">
          AEO/GEO Score Auditor
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

        <ProfileSelector
          value={siteProfile}
          onChange={setSiteProfile}
          disabled={loading}
        />

        <label className="mb-6 flex items-start gap-3 rounded-lg border border-indigo-100 bg-indigo-50 px-4 py-3 text-sm text-stone-700">
          <input
            type="checkbox"
            checked={llmPromptEval}
            onChange={(e) => setLlmPromptEval(e.target.checked)}
            disabled={loading}
            className="mt-1 h-4 w-4 rounded text-indigo-600 focus:ring-indigo-500"
          />
          <span>
            <span className="block font-semibold text-stone-900">
              LLM-check prompt answers
            </span>
            <span className="text-xs text-stone-500">
              Uses OpenAI when configured to judge whether retrieved site evidence truly answers each prompt.
            </span>
          </span>
        </label>

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
            <div className="flex flex-col gap-4 sm:flex-row">
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
          <ReportBook
            result={auditResult}
            auditType="page"
            sourceUrl={url}
            detailedPDF={detailedPDF}
            onDetailedPDFChange={setDetailedPDF}
            onDownloadPDF={() => downloadPDF(auditResult, 'page')}
          />
        )}

        {/* Domain Results */}
        {domainResult && (
          <ReportBook
            result={domainResult}
            auditType="domain"
            sourceUrl={domain}
            detailedPDF={detailedPDF}
            onDetailedPDFChange={setDetailedPDF}
            onDownloadPDF={() => downloadPDF(domainResult, 'domain')}
          />
        )}
      </div>
    </main>
  );
}
