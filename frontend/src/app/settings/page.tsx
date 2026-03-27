'use client'

import { useState, useEffect } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { Card, CardHeader } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { healthApi, marketDataApi } from '@/lib/api'

interface HealthData {
  status?: string
  version?: string
  uptime_seconds?: number
  db?: string
  redis?: string
}

interface PairData {
  pair: string
  timeframe?: string
}

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [pairs, setPairs] = useState<PairData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetch = async () => {
      try {
        const [healthRes, pairsRes] = await Promise.allSettled([
          healthApi.getHealth(),
          marketDataApi.getPairs(),
        ])
        if (healthRes.status === 'fulfilled') setHealth(healthRes.value.data)
        if (pairsRes.status === 'fulfilled') setPairs(pairsRes.value.data || [])
      } catch {
        // ignore
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [])

  const envSettings = [
    { key: 'TRACKED_PAIRS', value: 'XBT/USD, ETH/USD, SOL/USD' },
    { key: 'PRIMARY_TIMEFRAME', value: '1m' },
    { key: 'PAPER_INITIAL_BALANCE', value: '$100,000.00' },
    { key: 'PAPER_TAKER_FEE', value: '0.26%' },
    { key: 'PAPER_MAKER_FEE', value: '0.16%' },
    { key: 'PAPER_SLIPPAGE_BPS', value: '5 bps' },
    { key: 'MAX_CONCURRENT_POSITIONS', value: '5' },
    { key: 'MAX_DAILY_LOSS_PCT', value: '5%' },
    { key: 'RISK_PER_TRADE_PCT', value: '2%' },
    { key: 'KRAKEN_API_BASE', value: 'https://api.kraken.com' },
    { key: 'ENV', value: 'production' },
    { key: 'LOG_LEVEL', value: 'INFO' },
  ]

  return (
    <AppShell>
      <div className="space-y-6">
        <h2 className="text-xl font-bold">Settings</h2>

        {/* System health */}
        <Card>
          <CardHeader title="System Health" />
          {loading ? (
            <div className="h-20 animate-pulse bg-border rounded" />
          ) : health ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-muted uppercase tracking-wider mb-1">Status</p>
                <Badge variant={health.status === 'ok' ? 'success' : 'danger'}>{health.status ?? '—'}</Badge>
              </div>
              <div>
                <p className="text-xs text-muted uppercase tracking-wider mb-1">Database</p>
                <Badge variant={health.db === 'ok' ? 'success' : 'danger'}>{health.db ?? '—'}</Badge>
              </div>
              <div>
                <p className="text-xs text-muted uppercase tracking-wider mb-1">Redis</p>
                <Badge variant={health.redis === 'ok' ? 'success' : 'danger'}>{health.redis ?? '—'}</Badge>
              </div>
              <div>
                <p className="text-xs text-muted uppercase tracking-wider mb-1">Uptime</p>
                <p className="text-sm">{health.uptime_seconds != null ? `${Math.floor(health.uptime_seconds / 60)}m` : '—'}</p>
              </div>
            </div>
          ) : (
            <p className="text-muted text-sm">Backend unavailable</p>
          )}
        </Card>

        {/* Tracked pairs */}
        <Card>
          <CardHeader title="Tracked Pairs" subtitle="Configured via TRACKED_PAIRS env var" />
          <div className="flex flex-wrap gap-2">
            {pairs.length > 0
              ? pairs.map((p) => (
                  <span key={typeof p === 'string' ? p : p.pair} className="px-3 py-1.5 bg-background border border-border rounded text-sm font-mono">
                    {typeof p === 'string' ? p : p.pair}
                  </span>
                ))
              : ['XBT/USD', 'ETH/USD', 'SOL/USD'].map((p) => (
                  <span key={p} className="px-3 py-1.5 bg-background border border-border rounded text-sm font-mono text-muted">
                    {p}
                  </span>
                ))}
          </div>
        </Card>

        {/* Environment config */}
        <Card>
          <CardHeader title="Configuration" subtitle="Read from environment variables — edit .env to change" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {envSettings.map(({ key, value }) => (
              <div key={key} className="flex justify-between items-center p-2.5 bg-background rounded border border-border">
                <span className="text-xs font-mono text-muted">{key}</span>
                <span className="text-xs text-white font-medium">{value}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Disclaimer */}
        <Card className="border-yellow-500/30 bg-yellow-500/5">
          <div className="flex gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="font-bold text-yellow-400 mb-1">Paper Trading System</p>
              <p className="text-sm text-yellow-200/70">
                This is a simulation platform only. It uses Kraken&apos;s public market data API.
                No real orders are placed. No real money is involved. For research and educational purposes only.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </AppShell>
  )
}
