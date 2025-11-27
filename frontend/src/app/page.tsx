'use client'

import { useState } from 'react'

export default function Home() {
  const [url, setUrl] = useState('')
  const [includeAI, setIncludeAI] = useState(true)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!url) {
      setError('Please enter a URL')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      console.log('Sending audit request to backend...')
      const response = await fetch('http://localhost:8000/api/v1/audit/page', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          options: {
            include_ai_citation: includeAI,
            wait_for_completion: true,
          }
        })
      })

      console.log('Response status:', response.status)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(`Audit failed: ${response.status} - ${JSON.stringify(errorData)}`)
      }

      const data = await response.json()
      console.log('Audit result:', data)
      setResult(data)
    } catch (err: any) {
      console.error('Audit error:', err)
      setError(err.message || 'Failed to audit page. Make sure the backend is running on port 8000.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            AEO Score Auditor
          </h1>
          <p className="text-xl text-gray-600">
            Analyze and optimize content for AI-powered search engines
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-semibold mb-4">Quick Audit</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enter URL to audit:
              </label>
              <input
                type="url"
                placeholder="https://example.com/page"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={loading}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-gray-100"
              />
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="ai-citation"
                checked={includeAI}
                onChange={(e) => setIncludeAI(e.target.checked)}
                disabled={loading}
                className="mr-2"
              />
              <label htmlFor="ai-citation" className="text-sm text-gray-700">
                Include AI Citation Analysis (adds 2-3 minutes)
              </label>
            </div>
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}
            <button 
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 text-white py-3 px-6 rounded-md hover:bg-indigo-700 transition-colors font-semibold disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Auditing...' : 'Audit Now'}
            </button>
          </form>
        </div>

        {result && (
          <div className="bg-white rounded-lg shadow-md p-8 mb-8">
            <h2 className="text-2xl font-semibold mb-4">Audit Results</h2>
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm text-gray-600">Overall Score</p>
                  <p className="text-5xl font-bold text-indigo-600">
                    {result.result?.overall_score || result.overall_score}
                  </p>
                  <p className="text-xl text-gray-700">
                    Grade: {result.result?.grade || result.grade}
                  </p>
                </div>
              </div>
              {result.result?.note && (
                <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded mb-4">
                  <p className="font-semibold">Note:</p>
                  <p>{result.result.note}</p>
                </div>
              )}
            </div>
            <div className="space-y-3">
              <h3 className="font-semibold text-lg">Score Breakdown</h3>
              {result.result?.breakdown && Object.entries(result.result.breakdown).map(([key, value]: [string, any]) => (
                <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <span className="capitalize">{key.replace(/_/g, ' ')}</span>
                  <span className="font-semibold">{value.score}/{value.max}</span>
                </div>
              ))}
            </div>
          </div>
        )}


        {!result && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-2 text-gray-900">
                Scoring Framework
              </h3>
              <p className="text-gray-600 text-sm">
                7 weighted buckets analyzing answerability, structured data, authority, and more
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-2 text-gray-900">
                AI Citation Analysis
              </h3>
              <p className="text-gray-600 text-sm">
                Test with GPT-4, Gemini, and Perplexity to measure real AI usage
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-2 text-gray-900">
                Actionable Recommendations
              </h3>
              <p className="text-gray-600 text-sm">
                Get specific fixes with code snippets and prioritized by impact
              </p>
            </div>
          </div>
        )}

        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Backend API: <a href="http://localhost:8000/health" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">Check Status</a></p>
          <p className="mt-2">API Docs: <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">http://localhost:8000/docs</a></p>
        </div>
      </div>
    </main>
  )
}

