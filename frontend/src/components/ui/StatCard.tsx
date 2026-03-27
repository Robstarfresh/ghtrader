import { cn, formatCurrency, formatPercent } from '@/lib/utils'
import { Card } from './Card'

interface StatCardProps {
  label: string
  value: string | number | null | undefined
  change?: number | null
  changeLabel?: string
  format?: 'currency' | 'percent' | 'number' | 'raw'
  loading?: boolean
}

export function StatCard({ label, value, change, changeLabel, format = 'raw', loading }: StatCardProps) {
  const displayValue = () => {
    if (loading) return '...'
    if (value == null) return '—'
    if (format === 'currency' && typeof value === 'number') return formatCurrency(value)
    if (format === 'percent' && typeof value === 'number') return formatPercent(value)
    return String(value)
  }

  return (
    <Card>
      <p className="text-xs font-semibold text-muted uppercase tracking-wider mb-1">{label}</p>
      <p className={cn('text-2xl font-bold', loading && 'text-muted')}>{displayValue()}</p>
      {change != null && (
        <p className={cn('text-xs mt-1', change >= 0 ? 'text-green-400' : 'text-red-400')}>
          {formatPercent(change)} {changeLabel && <span className="text-muted">{changeLabel}</span>}
        </p>
      )}
    </Card>
  )
}
