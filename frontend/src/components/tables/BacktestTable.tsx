import { formatCurrency, formatPercent, formatDate, cn } from '@/lib/utils'
import { Badge } from '@/components/ui/Badge'
import { TableSkeleton } from '@/components/ui/LoadingSkeleton'

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

interface BacktestTableProps {
  backtests: BacktestRun[]
  loading?: boolean
}

export function BacktestTable({ backtests, loading }: BacktestTableProps) {
  if (loading) return <TableSkeleton rows={4} cols={8} />

  if (!backtests || backtests.length === 0) {
    return <p className="text-muted text-sm py-4">No backtests run yet</p>
  }

  const statusVariant = (status: string): 'success' | 'warning' | 'danger' | 'muted' => {
    if (status === 'completed') return 'success'
    if (status === 'running') return 'warning'
    if (status === 'failed') return 'danger'
    return 'muted'
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-muted text-xs uppercase tracking-wider border-b border-border">
            <th className="text-left py-2 pr-4">Name</th>
            <th className="text-left py-2 pr-4">Strategy</th>
            <th className="text-left py-2 pr-4">Pair</th>
            <th className="text-left py-2 pr-4">Period</th>
            <th className="text-right py-2 pr-4">Net PnL</th>
            <th className="text-right py-2 pr-4">Return</th>
            <th className="text-right py-2 pr-4">Win Rate</th>
            <th className="text-right py-2 pr-4">Sharpe</th>
            <th className="text-left py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {backtests.map((bt) => (
            <tr key={bt.id} className="border-b border-border/50 hover:bg-white/5">
              <td className="py-2 pr-4 font-medium">{bt.name}</td>
              <td className="py-2 pr-4 text-muted">{bt.strategy_name}</td>
              <td className="py-2 pr-4">{bt.pair}</td>
              <td className="py-2 pr-4 text-xs text-muted">
                {formatDate(bt.start_date)} → {formatDate(bt.end_date)}
              </td>
              <td className={cn('py-2 pr-4 text-right font-medium', (bt.net_pnl ?? 0) >= 0 ? 'text-green-400' : 'text-red-400')}>
                {formatCurrency(bt.net_pnl)}
              </td>
              <td className={cn('py-2 pr-4 text-right', (bt.total_return_pct ?? 0) >= 0 ? 'text-green-400' : 'text-red-400')}>
                {formatPercent(bt.total_return_pct)}
              </td>
              <td className="py-2 pr-4 text-right">
                {bt.win_rate != null ? `${(bt.win_rate * 100).toFixed(1)}%` : '—'}
              </td>
              <td className="py-2 pr-4 text-right">
                {bt.sharpe_ratio != null ? bt.sharpe_ratio.toFixed(2) : '—'}
              </td>
              <td className="py-2">
                <Badge variant={statusVariant(bt.status)}>{bt.status}</Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
