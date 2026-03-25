'use client'

import { useState, useEffect } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { Card, CardHeader } from '@/components/ui/Card'
import { riskApi } from '@/lib/api'
import { formatPercent, formatCurrency } from '@/lib/utils'

interface RiskStatus {
  kill_switch_active?: boolean
  daily_loss?: number
  daily_loss_pct?: number
  open_positions_count?: number
  max_daily_loss_pct?: number
  max_concurrent_positions?: number
  risk_per_trade_pct?: number
  total_exposure?: number
}

export default function RiskPage() {
  const [risk, setRisk] = useState<RiskStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [resetting, setResetting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchRisk = async () => {
    try {
      const res = await riskApi.getStatus()
      setRisk(res.data)
      setError(null)
    } catch {
      setError('Failed to load risk status')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRisk()
    const interval = setInterval(fetchRisk, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleReset = async () => {
    if (!confirm('Reset risk controls? This will clear the daily loss counter and kill switch.')) return
    setResetting(true)
    try {
      await riskApi.reset()
      await fetchRisk()
    } catch {
      setError('Failed to reset risk')
    } finally {
      setResetting(false)
    }
  }

  const metrics = risk
    ? [
        { label: 'Kill Switch', value: risk.kill_switch_active ? '🔴 ACTIVE' : '🟢 Normal', highlight: risk.kill_switch_active },
        { label: 'Daily Loss ($)', value: formatCurrency(risk.daily_loss) },
        { label: 'Daily Loss %', value: formatPercent(risk.daily_loss_pct) },
        { label: 'Max Daily Loss %', value: formatPercent(risk.max_daily_loss_pct) },
        { label: 'Open Positions', value: `${risk.open_positions_count ?? 0} / ${risk.max_concurrent_positions ?? '—'}` },
        { label: 'Risk Per Trade', value: formatPercent(risk.risk_per_trade_pct) },
        { label: 'Total Exposure', value: formatCurrency(risk.total_exposure) },
      ]
    : []

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold">Risk Management</h2>
          <button
            onClick={handleReset}
            disabled={resetting}
            className="px-4 py-2 bg-red-500/20 text-red-400 border border-red-500/30 rounded text-sm hover:bg-red-500/30 disabled:opacity-50"
          >
            {resetting ? 'Resetting...' : 'Reset Risk Controls'}
          </button>
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-20 animate-pulse bg-surface border border-border rounded-lg" />
            ))}
          </div>
        ) : (
          <>
            {risk?.kill_switch_active && (
              <Card className="border-red-500/50 bg-red-500/10">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🔴</span>
                  <div>
                    <p className="font-bold text-red-400">Kill Switch Active</p>
                    <p className="text-sm text-red-300">
                      Daily loss limit has been reached. No new positions will be opened. Reset to resume trading.
                    </p>
                  </div>
                </div>
              </Card>
            )}

            <Card>
              <CardHeader title="Risk Metrics" />
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {metrics.map(({ label, value, highlight }) => (
                  <div key={label} className="p-3 bg-background rounded border border-border">
                    <p className="text-xs text-muted uppercase tracking-wider mb-1">{label}</p>
                    <p className={`font-semibold ${highlight ? 'text-red-400' : 'text-white'}`}>{value}</p>
                  </div>
                ))}
              </div>
            </Card>

            <Card>
              <CardHeader title="Risk Configuration" subtitle="Set via environment variables" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                {[
                  ['MAX_DAILY_LOSS_PCT', '0.05 (5%)'],
                  ['MAX_CONCURRENT_POSITIONS', '5'],
                  ['RISK_PER_TRADE_PCT', '0.02 (2%)'],
                  ['PAPER_TAKER_FEE', '0.26%'],
                  ['PAPER_MAKER_FEE', '0.16%'],
                  ['PAPER_SLIPPAGE_BPS', '5 bps'],
                ].map(([key, val]) => (
                  <div key={key} className="flex justify-between p-2 bg-background rounded border border-border">
                    <span className="text-muted font-mono text-xs">{key}</span>
                    <span className="text-white text-xs">{val}</span>
                  </div>
                ))}
              </div>
            </Card>
          </>
        )}
      </div>
    </AppShell>
  )
}
