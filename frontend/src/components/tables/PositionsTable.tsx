import { formatCurrency, formatNumber, cn } from '@/lib/utils'
import { Badge } from '@/components/ui/Badge'
import { TableSkeleton } from '@/components/ui/LoadingSkeleton'

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

interface PositionsTableProps {
  positions: Position[]
  loading?: boolean
}

export function PositionsTable({ positions, loading }: PositionsTableProps) {
  if (loading) return <TableSkeleton rows={4} cols={8} />

  if (!positions || positions.length === 0) {
    return <p className="text-muted text-sm py-4">No open positions</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-muted text-xs uppercase tracking-wider border-b border-border">
            <th className="text-left py-2 pr-4">Pair</th>
            <th className="text-left py-2 pr-4">Side</th>
            <th className="text-right py-2 pr-4">Qty</th>
            <th className="text-right py-2 pr-4">Entry</th>
            <th className="text-right py-2 pr-4">Current</th>
            <th className="text-right py-2 pr-4">Unreal. PnL</th>
            <th className="text-right py-2 pr-4">Stop Loss</th>
            <th className="text-right py-2">Take Profit</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((pos) => (
            <tr key={pos.id} className="border-b border-border/50 hover:bg-white/5">
              <td className="py-2 pr-4 font-medium">{pos.pair}</td>
              <td className="py-2 pr-4">
                <Badge variant={pos.side === 'buy' ? 'success' : 'danger'}>
                  {pos.side.toUpperCase()}
                </Badge>
              </td>
              <td className="py-2 pr-4 text-right">{formatNumber(pos.quantity)}</td>
              <td className="py-2 pr-4 text-right">{formatCurrency(pos.entry_price)}</td>
              <td className="py-2 pr-4 text-right">{formatCurrency(pos.current_price)}</td>
              <td className={cn('py-2 pr-4 text-right font-medium', (pos.unrealized_pnl ?? 0) >= 0 ? 'text-green-400' : 'text-red-400')}>
                {formatCurrency(pos.unrealized_pnl)}
              </td>
              <td className="py-2 pr-4 text-right text-muted">{pos.stop_loss ? formatCurrency(pos.stop_loss) : '—'}</td>
              <td className="py-2 text-right text-muted">{pos.take_profit ? formatCurrency(pos.take_profit) : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
