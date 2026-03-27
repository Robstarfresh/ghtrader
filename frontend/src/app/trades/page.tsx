'use client'

import { useState, useEffect } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { Card, CardHeader } from '@/components/ui/Card'
import { TradesTable } from '@/components/tables/TradesTable'
import { tradesApi } from '@/lib/api'

const PAGE_SIZE = 25

interface Trade {
  id: number
  pair: string
  side: string
  entry_price: number
  exit_price?: number
  quantity: number
  realized_pnl?: number
  fee_paid?: number
  exit_reason?: string
  opened_at: string
  closed_at?: string
}

export default function TradesPage() {
  const [trades, setTrades] = useState<Trade[]>([])
  const [page, setPage] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hasMore, setHasMore] = useState(true)

  useEffect(() => {
    const fetch = async () => {
      setLoading(true)
      try {
        const res = await tradesApi.getRecent(PAGE_SIZE, page * PAGE_SIZE)
        const data: Trade[] = res.data || []
        setTrades(data)
        setHasMore(data.length === PAGE_SIZE)
        setError(null)
      } catch {
        setError('Failed to load trades')
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [page])

  return (
    <AppShell>
      <div className="space-y-6">
        <h2 className="text-xl font-bold">Trades</h2>
        {error && <p className="text-red-400 text-sm">{error}</p>}

        <Card>
          <CardHeader title="Recent Trades" subtitle={`Page ${page + 1}`} />
          <TradesTable trades={trades} loading={loading} />

          <div className="flex justify-between items-center mt-4 pt-4 border-t border-border">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-3 py-1.5 text-sm bg-surface border border-border rounded hover:bg-white/5 disabled:opacity-40"
            >
              Previous
            </button>
            <span className="text-sm text-muted">Page {page + 1}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={!hasMore}
              className="px-3 py-1.5 text-sm bg-surface border border-border rounded hover:bg-white/5 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </Card>
      </div>
    </AppShell>
  )
}
