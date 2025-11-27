export default function Home() {
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
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enter URL to audit:
              </label>
              <input
                type="url"
                placeholder="https://example.com/page"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="ai-citation"
                className="mr-2"
              />
              <label htmlFor="ai-citation" className="text-sm text-gray-700">
                Include AI Citation Analysis (adds 2-3 minutes)
              </label>
            </div>
            <button className="w-full bg-indigo-600 text-white py-3 px-6 rounded-md hover:bg-indigo-700 transition-colors font-semibold">
              Audit Now
            </button>
          </div>
        </div>

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

        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Frontend is running! Backend API will be available at port 8000</p>
          <p className="mt-2">Check out the <a href="/docs" className="text-indigo-600 hover:underline">documentation</a> to get started</p>
        </div>
      </div>
    </main>
  )
}

