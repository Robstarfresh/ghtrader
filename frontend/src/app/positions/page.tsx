'use client'

import { useState, useEffect } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { Card, CardHeader } from '@/components/ui/Card'
import { PositionsTable } from '@/components/tables/PositionsTable'
import { TradesTable } from '@/components/tables/TradesTable'
import { positionsApi } from '@/lib/api'
import { cn } from '@/lib/utils'

type Tab = 'open' | 'history'

interface Position {
  id: number
  pair: string
  side: string
  quantity: number
  entry_price: number
  current_price?: number
  unrealized_pnl?: number
  stop_loss?: number
  take_profit?: number
}

interface ClosedPosition {
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

export default function PositionsPage() {
  const [tab, setTab] = useState<Tab>('open')
  const [open, setOpen] = useState<Position[]>([])
  const [history, setHistory] = useState<ClosedPosition[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetch = async () => {
      setLoading(true)
      try {
        const [openRes, histRes] = await Promise.allSettled([
          positionsApi.getOpen(),
          positionsApi.getHistory(),
        ])
        if (openRes.status === 'fulfilled') setOpen(openRes.value.data || [])
        if (histRes.status === 'fulfilled') setHistory(histRes.value.data || [])
        setError(null)
      } catch {
        setError('Failed to load positions')
      } finally {
        setLoading(false)
      }
    }
    fetch()
    const interval = setInterval(fetch, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <AppShell>
      <div className="space-y-6">
        <h2 className="text-xl font-bold">Positions</h2>
        {error && <p className="text-red-400 text-sm">{error}</p>}

        <div className="flex gap-2 border-b border-border">
          {(['open', 'history'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={cn(
                'px-4 py-2 text-sm font-medium border-b-2 transition-colors capitalize',
                tab === t
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted hover:text-white'
              )}
            >
              {t === 'open' ? `Open (${open.length})` : `History (${history.length})`}
            </button>
          ))}
        </div>

        <Card>
          <CardHeader title={tab === 'open' ? 'Open Positions' : 'Position History'} />
          {tab === 'open' ? (
            <PositionsTable positions={open} loading={loading} />
          ) : (
            <TradesTable trades={history} loading={loading} />
          )}
        </Card>
      </div>
    </AppShell>
  )
}
