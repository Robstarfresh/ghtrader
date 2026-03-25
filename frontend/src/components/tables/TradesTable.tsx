import { formatCurrency, formatNumber, formatDate, cn } from '@/lib/utils'
import { Badge } from '@/components/ui/Badge'
import { TableSkeleton } from '@/components/ui/LoadingSkeleton'

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

interface TradesTableProps {
  trades: Trade[]
  loading?: boolean
}

export function TradesTable({ trades, loading }: TradesTableProps) {
  if (loading) return <TableSkeleton rows={5} cols={8} />

  if (!trades || trades.length === 0) {
    return <p className="text-muted text-sm py-4">No trades yet</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-muted text-xs uppercase tracking-wider border-b border-border">
            <th className="text-left py-2 pr-4">Time</th>
            <th className="text-left py-2 pr-4">Pair</th>
            <th className="text-left py-2 pr-4">Side</th>
            <th className="text-right py-2 pr-4">Entry</th>
            <th className="text-right py-2 pr-4">Exit</th>
            <th className="text-right py-2 pr-4">Qty</th>
            <th className="text-right py-2 pr-4">PnL</th>
            <th className="text-right py-2 pr-4">Fees</th>
            <th className="text-left py-2">Reason</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((trade) => (
            <tr key={trade.id} className="border-b border-border/50 hover:bg-white/5">
              <td className="py-2 pr-4 text-muted text-xs">{formatDate(trade.closed_at || trade.opened_at)}</td>
              <td className="py-2 pr-4 font-medium">{trade.pair}</td>
              <td className="py-2 pr-4">
                <Badge variant={trade.side === 'buy' ? 'success' : 'danger'}>
                  {trade.side.toUpperCase()}
                </Badge>
              </td>
              <td className="py-2 pr-4 text-right">{formatCurrency(trade.entry_price)}</td>
              <td className="py-2 pr-4 text-right">{trade.exit_price ? formatCurrency(trade.exit_price) : '—'}</td>
              <td className="py-2 pr-4 text-right">{formatNumber(trade.quantity)}</td>
              <td className={cn('py-2 pr-4 text-right font-medium', (trade.realized_pnl ?? 0) >= 0 ? 'text-green-400' : 'text-red-400')}>
                {formatCurrency(trade.realized_pnl)}
              </td>
              <td className="py-2 pr-4 text-right text-muted">{formatCurrency(trade.fee_paid)}</td>
              <td className="py-2 text-xs text-muted">{trade.exit_reason ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
