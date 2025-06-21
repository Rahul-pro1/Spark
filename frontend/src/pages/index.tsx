// Basic Next.js frontend (frontend/src/pages/index.tsx)
import { useState } from 'react'

export default function Home() {
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setResponse('')
    try {
      const res = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })
      const data = await res.json()
      setResponse(data.response)
    } catch (err) {
      console.error(err)
      setResponse('Error connecting to backend')
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-10 text-center">
      <h1 className="text-3xl font-bold mb-4">Smart DemandSense</h1>
      <form onSubmit={handleSubmit} className="space-x-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="px-4 py-2 border rounded-md w-2/3"
          placeholder="Ask a question about demand..."
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-500 text-white rounded-md"
          disabled={loading}
        >
          {loading ? 'Generating...' : 'Ask'}
        </button>
      </form>
      {response && (
        <div className="mt-6 p-4 bg-white shadow rounded text-left max-w-3xl mx-auto">
          <h2 className="font-semibold text-lg mb-2">Response:</h2>
          <p>{response}</p>
        </div>
      )}
    </div>
  )
}
