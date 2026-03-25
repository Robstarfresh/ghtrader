'use client'

import { useState, useEffect, useCallback } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { Card, CardHeader } from '@/components/ui/Card'
import { StatCard } from '@/components/ui/StatCard'
import { EquityCurve } from '@/components/charts/EquityCurve'
import { PositionsTable } from '@/components/tables/PositionsTable'
import { TradesTable } from '@/components/tables/TradesTable'
import { pnlApi, positionsApi, tradesApi, riskApi } from '@/lib/api'
import { formatPercent } from '@/lib/utils'

interface PnlSummary {
  initial_balance?: number
  current_equity?: number
  total_pnl?: number
  total_return_pct?: number
  daily_pnl?: number
  daily_pnl_pct?: number
  win_rate?: number
  total_trades?: number
}

interface EquityPoint {
  timestamp: string
  equity: number
}

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

interface RiskStatus {
  kill_switch_active?: boolean
  daily_loss_pct?: number
  open_positions_count?: number
}

export default function DashboardPage() {
  const [pnl, setPnl] = useState<PnlSummary | null>(null)
  const [equityCurve, setEquityCurve] = useState<EquityPoint[]>([])
  const [positions, setPositions] = useState<Position[]>([])
  const [trades, setTrades] = useState<Trade[]>([])
  const [risk, setRisk] = useState<RiskStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAll = useCallback(async () => {
    try {
      const [pnlRes, curveRes, posRes, tradesRes, riskRes] = await Promise.allSettled([
        pnlApi.getSummary(),
        pnlApi.getEquityCurve(),
        positionsApi.getOpen(),
        tradesApi.getRecent(10),
        riskApi.getStatus(),
      ])

      if (pnlRes.status === 'fulfilled') setPnl(pnlRes.value.data)
      if (curveRes.status === 'fulfilled') setEquityCurve(curveRes.value.data || [])
      if (posRes.status === 'fulfilled') setPositions(posRes.value.data || [])
      if (tradesRes.status === 'fulfilled') setTrades(tradesRes.value.data || [])
      if (riskRes.status === 'fulfilled') setRisk(riskRes.value.data)
      setError(null)
    } catch {
      setError('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, 5000)
    return () => clearInterval(interval)
  }, [fetchAll])

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold">Dashboard</h2>
          {error && <p className="text-red-400 text-sm">{error}</p>}
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Balance"
            value={pnl?.initial_balance}
            format="currency"
            loading={loading}
          />
          <StatCard
            label="Equity"
            value={pnl?.current_equity}
            format="currency"
            change={pnl?.total_return_pct}
            changeLabel="total"
            loading={loading}
          />
          <StatCard
            label="Daily PnL"
            value={pnl?.daily_pnl}
            format="currency"
            change={pnl?.daily_pnl_pct}
            loading={loading}
          />
          <StatCard
            label="Win Rate"
            value={pnl?.win_rate != null ? formatPercent(pnl.win_rate * 100, 1) : null}
            loading={loading}
          />
        </div>

        {/* Equity curve */}
        <Card>
          <CardHeader title="Equity Curve" />
          <EquityCurve data={equityCurve} loading={loading} />
        </Card>

        {/* Positions + Trades */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <Card>
            <CardHeader title="Open Positions" subtitle={`${positions.length} active`} />
            <PositionsTable positions={positions} loading={loading} />
          </Card>
          <Card>
            <CardHeader title="Recent Trades" subtitle="Last 10" />
            <TradesTable trades={trades} loading={loading} />
          </Card>
        </div>

        {/* Risk Status */}
        {risk && (
          <Card>
            <CardHeader title="Risk Status" />
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-muted text-xs uppercase tracking-wider mb-1">Kill Switch</p>
                <p className={risk.kill_switch_active ? 'text-red-400 font-bold' : 'text-green-400'}>
                  {risk.kill_switch_active ? '🔴 ACTIVE' : '🟢 Normal'}
                </p>
              </div>
              <div>
                <p className="text-muted text-xs uppercase tracking-wider mb-1">Daily Loss</p>
                <p className={(risk.daily_loss_pct ?? 0) < -3 ? 'text-red-400' : 'text-white'}>
                  {formatPercent(risk.daily_loss_pct)}
                </p>
              </div>
              <div>
                <p className="text-muted text-xs uppercase tracking-wider mb-1">Open Positions</p>
                <p>{risk.open_positions_count ?? 0}</p>
              </div>
            </div>
          </Card>
        )}
      </div>
    </AppShell>
  )
}
