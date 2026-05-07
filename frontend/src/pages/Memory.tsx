import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { memoryService } from '../services/api'

export default function MemoryPage() {
  const [inputText, setInputText] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [source, setSource] = useState('')
  const [results, setResults] = useState<any[]>([])

  const { data: stats } = useQuery({
    queryKey: ['memory-stats'],
    queryFn: memoryService.getStats,
  })

  const ingestMutation = useMutation({
    mutationFn: () =>
      memoryService.ingest({
        text: inputText,
        source: source || undefined,
      }),
    onSuccess: () => {
      setInputText('')
      setSource('')
    },
  })

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    const searchResults = await memoryService.search(searchQuery)
    setResults(searchResults)
  }

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-titanium-100">Memory</h2>
        <p className="text-titanium-400 mt-1">Document ingestion and retrieval</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-titanium-100 mb-4">Ingest Document</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-titanium-300 mb-1">Source (optional)</label>
              <input
                type="text"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                placeholder="document.pdf, webpage, etc."
                className="input-primary w-full"
              />
            </div>

            <div>
              <label className="block text-sm text-titanium-300 mb-1">Content</label>
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Paste document content here..."
                className="input-primary w-full h-48 resize-none"
              />
            </div>

            <button
              className="btn-primary w-full"
              disabled={!inputText.trim() || ingestMutation.isPending}
              onClick={() => ingestMutation.mutate()}
            >
              {ingestMutation.isPending ? 'Processing...' : 'Ingest Document'}
            </button>

            {ingestMutation.isSuccess && (
              <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400 text-sm">
                Document ingested successfully! ({ingestMutation.data.chunks_stored} chunks stored)
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-titanium-100 mb-4">Search Memory</h3>

          <div className="space-y-4">
            <div className="flex gap-3">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search for relevant context..."
                className="input-primary flex-1"
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
              <button
                className="btn-secondary"
                onClick={handleSearch}
                disabled={!searchQuery.trim()}
              >
                Search
              </button>
            </div>

            <div className="space-y-3 max-h-64 overflow-y-auto">
              {results.map((result, i) => (
                <div key={i} className="p-4 bg-titanium-900 rounded-lg border border-titanium-700">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-accent-400">Score: {result.score?.toFixed(3)}</span>
                    <span className="text-xs text-titanium-500">#{result.rank}</span>
                  </div>
                  <p className="text-sm text-titanium-200 line-clamp-3">{result.text}</p>
                </div>
              ))}

              {results.length === 0 && searchQuery && (
                <p className="text-titanium-500 text-center py-8">No results found</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {stats && (
        <div className="card mt-6">
          <h3 className="text-lg font-semibold text-titanium-100 mb-4">System Info</h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-titanium-400">Chunker</p>
              <p className="text-titanium-200">{String(stats.chunker)}</p>
            </div>
            <div>
              <p className="text-sm text-titanium-400">Embedder</p>
              <p className="text-titanium-200">{String(stats.embedder)}</p>
            </div>
            <div>
              <p className="text-sm text-titanium-400">Vector Store</p>
              <p className="text-titanium-200">{String(stats.vector_store)}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
