'use client'

import { useState, useEffect } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { Card, CardHeader } from '@/components/ui/Card'
import { BacktestTable } from '@/components/tables/BacktestTable'
import { backtestApi, BacktestConfig } from '@/lib/api'
import { formatPercent } from '@/lib/utils'

interface BacktestRun {
  id: number
  name: string
  strategy_name: string
  pair: string
  start_date: string
  end_date: string
  net_pnl?: number
  total_return_pct?: number
  win_rate?: number
  sharpe_ratio?: number
  status: string
}

interface LeaderboardEntry {
  strategy_name: string
  total_return_pct?: number
  win_rate?: number
  sharpe_ratio?: number
  run_count?: number
}

const STRATEGIES = ['macd', 'rsi', 'vwap', 'breakout', 'combined']
const PAIRS = ['XBT/USD', 'ETH/USD', 'SOL/USD']
const TIMEFRAMES = ['1m', '5m', '15m', '1h']

export default function BacktestsPage() {
  const [backtests, setBacktests] = useState<BacktestRun[]>([])
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [form, setForm] = useState<BacktestConfig>({
    name: '',
    strategy_name: 'combined',
    pair: 'XBT/USD',
    timeframe: '1m',
    start_date: '2024-01-01T00:00:00',
    end_date: '2024-03-01T00:00:00',
    initial_balance: 100000,
  })

  const fetchData = async () => {
    try {
      const [listRes, lbRes] = await Promise.allSettled([
        backtestApi.list(),
        backtestApi.getLeaderboard(),
      ])
      if (listRes.status === 'fulfilled') setBacktests(listRes.value.data || [])
      if (lbRes.status === 'fulfilled') setLeaderboard(lbRes.value.data || [])
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    setSuccess(null)
    try {
      await backtestApi.run(form)
      setSuccess('Backtest started!')
      await fetchData()
    } catch {
      setError('Failed to start backtest')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <h2 className="text-xl font-bold">Backtests</h2>

        {/* Run backtest form */}
        <Card>
          <CardHeader title="Run New Backtest" />
          <form onSubmit={handleSubmit} className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-muted uppercase tracking-wider">Name</label>
              <input
                className="w-full mt-1 bg-background border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
                placeholder="my-backtest"
              />
            </div>
            <div>
              <label className="text-xs text-muted uppercase tracking-wider">Strategy</label>
              <select
                className="w-full mt-1 bg-background border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
                value={form.strategy_name}
                onChange={(e) => setForm({ ...form, strategy_name: e.target.value })}
              >
                {STRATEGIES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-muted uppercase tracking-wider">Pair</label>
              <select
                className="w-full mt-1 bg-background border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
                value={form.pair}
                onChange={(e) => setForm({ ...form, pair: e.target.value })}
              >
                {PAIRS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-muted uppercase tracking-wider">Timeframe</label>
              <select
                className="w-full mt-1 bg-background border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
                value={form.timeframe}
                onChange={(e) => setForm({ ...form, timeframe: e.target.value })}
              >
                {TIMEFRAMES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-muted uppercase tracking-wider">Start Date</label>
              <input
                type="datetime-local"
                className="w-full mt-1 bg-background border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
                value={form.start_date.replace('T00:00:00', '')}
                onChange={(e) => setForm({ ...form, start_date: `${e.target.value}:00` })}
              />
            </div>
            <div>
              <label className="text-xs text-muted uppercase tracking-wider">End Date</label>
              <input
                type="datetime-local"
                className="w-full mt-1 bg-background border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
                value={form.end_date.replace('T00:00:00', '')}
                onChange={(e) => setForm({ ...form, end_date: `${e.target.value}:00` })}
              />
            </div>
            <div>
              <label className="text-xs text-muted uppercase tracking-wider">Initial Balance ($)</label>
              <input
                type="number"
                className="w-full mt-1 bg-background border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
                value={form.initial_balance}
                onChange={(e) => setForm({ ...form, initial_balance: Number(e.target.value) })}
              />
            </div>
            <div className="col-span-2 lg:col-span-3 flex items-center gap-4">
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 bg-primary hover:bg-primary/80 rounded text-sm font-medium disabled:opacity-50"
              >
                {submitting ? 'Starting...' : 'Run Backtest'}
              </button>
              {success && <p className="text-green-400 text-sm">{success}</p>}
              {error && <p className="text-red-400 text-sm">{error}</p>}
            </div>
          </form>
        </Card>

        {/* Leaderboard */}
        {leaderboard.length > 0 && (
          <Card>
            <CardHeader title="Strategy Leaderboard" />
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-muted text-xs uppercase tracking-wider border-b border-border">
                    <th className="text-left py-2 pr-4">Strategy</th>
                    <th className="text-right py-2 pr-4">Avg Return</th>
                    <th className="text-right py-2 pr-4">Win Rate</th>
                    <th className="text-right py-2 pr-4">Sharpe</th>
                    <th className="text-right py-2">Runs</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.map((entry) => (
                    <tr key={entry.strategy_name} className="border-b border-border/50 hover:bg-white/5">
                      <td className="py-2 pr-4 font-medium">{entry.strategy_name}</td>
                      <td className={`py-2 pr-4 text-right ${(entry.total_return_pct ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {formatPercent(entry.total_return_pct)}
                      </td>
                      <td className="py-2 pr-4 text-right">
                        {entry.win_rate != null ? `${(entry.win_rate * 100).toFixed(1)}%` : '—'}
                      </td>
                      <td className="py-2 pr-4 text-right">
                        {entry.sharpe_ratio != null ? entry.sharpe_ratio.toFixed(2) : '—'}
                      </td>
                      <td className="py-2 text-right text-muted">{entry.run_count ?? 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Backtest list */}
        <Card>
          <CardHeader title="Backtest History" />
          <BacktestTable backtests={backtests} loading={loading} />
        </Card>
      </div>
    </AppShell>
  )
}
