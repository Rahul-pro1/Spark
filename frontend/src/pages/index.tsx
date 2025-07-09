import { useState } from "react"
import ReactMarkdown from 'react-markdown';

export default function Home() {
  const [query, setQuery] = useState("")
  const [location, setLocation] = useState("Texas")
  const [skuId, setSkuId] = useState("GATORADE-TX-32OZ")

  const [response, setResponse] = useState("")
  const [forecast, setForecast] = useState<{
    sku: string
    predicted_demand: number
    confidence: number
  } | null>(null)
  const [explanation, setExplanation] = useState<
    { source: string; snippet: string }[]
  >([])

  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setResponse("")
    setForecast(null)
    setExplanation([])
    try {
      const res = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, location, sku_id: skuId }),
      })
      const data = await res.json()
      setResponse(data.response)
      setForecast(data.forecast)
      setExplanation(data.explanation)
    } catch (err) {
      console.error(err)
      setResponse("Error connecting to backend")
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-[#f5f7fa] px-4 py-8">
      <div className="max-w-3xl mx-auto bg-white p-6 rounded-2xl shadow-md">
        <h1 className="text-3xl font-bold mb-4 text-blue-600 text-center">
          Smart DemandSense
        </h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
            placeholder="Ask a question about demand..."
          />
          <div className="grid grid-cols-2 gap-4">
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full px-4 py-2 border rounded-md focus:outline-none"
              placeholder="Enter store location (e.g., Texas)"
            />
            <input
              type="text"
              value={skuId}
              onChange={(e) => setSkuId(e.target.value)}
              className="w-full px-4 py-2 border rounded-md focus:outline-none"
              placeholder="Enter SKU ID"
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-md font-semibold transition"
            disabled={loading}
          >
            {loading ? "Generating..." : "Submit Query"}
          </button>
        </form>

        {response && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-2 text-gray-700">LLM Response</h2>
            <ReactMarkdown>
              {response}
            </ReactMarkdown>
          </div>
        )}

        {forecast && (
          <div className="mt-6">
            <h2 className="text-xl font-semibold mb-2 text-gray-700">
              SKU Forecast
            </h2>
            <div className="bg-blue-50 p-4 rounded-md text-gray-800">
              <p><strong>SKU:</strong> {forecast.sku}</p>
              <p><strong>Predicted Demand:</strong> {forecast.predicted_demand} units</p>
              <p><strong>Confidence:</strong> {forecast.confidence}%</p>
            </div>
          </div>
        )}

        {explanation.length > 0 && (
          <div className="mt-6">
            <h2 className="text-xl font-semibold mb-2 text-gray-700">
              Explanation Snippets
            </h2>
            <ul className="space-y-2 text-gray-800">
              {explanation.map((item, idx) => (
                <li key={idx} className="bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded-md">
                  <p className="text-sm text-gray-600">Source: {item.source}</p>
                  <p className="mt-1">{item.snippet}</p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
