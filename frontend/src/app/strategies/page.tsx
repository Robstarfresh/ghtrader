'use client'

import { useState, useEffect } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { Card, CardHeader } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { strategiesApi } from '@/lib/api'

interface Strategy {
  id: number
  name: string
  description?: string
  params?: Record<string, unknown>
  is_active: boolean
}

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [toggling, setToggling] = useState<number | null>(null)

  const fetchStrategies = async () => {
    try {
      const res = await strategiesApi.list()
      setStrategies(res.data || [])
      setError(null)
    } catch {
      setError('Failed to load strategies')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStrategies()
  }, [])

  const toggleStrategy = async (strategy: Strategy) => {
    setToggling(strategy.id)
    try {
      await strategiesApi.update(strategy.id, { is_active: !strategy.is_active })
      await fetchStrategies()
    } catch {
      setError('Failed to update strategy')
    } finally {
      setToggling(null)
    }
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <h2 className="text-xl font-bold">Strategies</h2>
        {error && <p className="text-red-400 text-sm">{error}</p>}

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-32 animate-pulse bg-surface border border-border rounded-lg" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {strategies.map((strategy) => (
              <Card key={strategy.id}>
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-white capitalize">{strategy.name}</h3>
                    {strategy.description && (
                      <p className="text-sm text-muted mt-0.5">{strategy.description}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={strategy.is_active ? 'success' : 'muted'}>
                      {strategy.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                    <button
                      onClick={() => toggleStrategy(strategy)}
                      disabled={toggling === strategy.id}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors disabled:opacity-50 ${
                        strategy.is_active ? 'bg-green-500' : 'bg-slate-600'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          strategy.is_active ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                </div>
                {strategy.params && Object.keys(strategy.params).length > 0 && (
                  <div className="mt-2 pt-2 border-t border-border">
                    <p className="text-xs text-muted uppercase tracking-wider mb-2">Parameters</p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(strategy.params).map(([key, val]) => (
                        <span key={key} className="text-xs bg-background border border-border rounded px-2 py-0.5">
                          <span className="text-muted">{key}:</span>{' '}
                          <span className="text-white">{String(val)}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  )
}
