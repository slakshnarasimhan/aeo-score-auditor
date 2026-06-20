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

export default function Home() {
  const [url, setUrl] = useState<string>('');
  const [domain, setDomain] = useState<string>('');
  const [maxPages, setMaxPages] = useState<number>(100);
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
