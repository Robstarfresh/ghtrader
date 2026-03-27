'use client'

import { useState, useEffect } from 'react'
import { engineApi, pnlApi } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'
import { Badge } from '@/components/ui/Badge'
import { Play, Square } from 'lucide-react'

interface EngineStatus {
  running: boolean
  equity?: number
}

interface PnlSummary {
  current_equity?: number
}

export function Header() {
  const [engineStatus, setEngineStatus] = useState<EngineStatus | null>(null)
  const [equity, setEquity] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchStatus = async () => {
    try {
      const [statusRes, pnlRes] = await Promise.all([
        engineApi.getStatus(),
        pnlApi.getSummary(),
      ])
      setEngineStatus(statusRes.data)
      const pnl = pnlRes.data as PnlSummary
      setEquity(pnl?.current_equity ?? null)
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  const toggleEngine = async () => {
    setLoading(true)
    try {
      if (engineStatus?.running) {
        await engineApi.stop()
      } else {
        await engineApi.start()
      }
      await fetchStatus()
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const isRunning = engineStatus?.running ?? false

  return (
    <header className="h-14 bg-surface border-b border-border flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <span
          className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}
        />
        <span className="text-sm text-muted">
          Engine: <span className={isRunning ? 'text-green-400' : 'text-red-400'}>{isRunning ? 'Running' : 'Stopped'}</span>
        </span>
      </div>

      <div className="flex items-center gap-4">
        {equity != null && (
          <span className="text-sm text-white font-medium">
            Equity: <span className="text-primary">{formatCurrency(equity)}</span>
          </span>
        )}
        <Badge variant="warning">PAPER TRADING</Badge>
        <button
          onClick={toggleEngine}
          disabled={loading}
          className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
            isRunning
              ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30'
              : 'bg-green-500/20 text-green-400 hover:bg-green-500/30 border border-green-500/30'
          } disabled:opacity-50`}
        >
          {isRunning ? <Square size={14} /> : <Play size={14} />}
          {loading ? 'Wait...' : isRunning ? 'Stop' : 'Start'}
        </button>
      </div>
    </header>
  )
}
