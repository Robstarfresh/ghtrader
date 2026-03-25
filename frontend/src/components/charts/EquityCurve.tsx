'use client'

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { formatCurrency } from '@/lib/utils'

interface DataPoint {
  timestamp: string
  equity: number
}

interface EquityCurveProps {
  data: DataPoint[]
  loading?: boolean
}

export function EquityCurve({ data, loading }: EquityCurveProps) {
  if (loading) {
    return <div className="h-64 animate-pulse bg-border rounded" />
  }

  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-muted text-sm">
        No equity curve data yet
      </div>
    )
  }

  const formatted = data.map((d) => ({
    ...d,
    label: new Date(d.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
  }))

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={formatted}>
        <defs>
          <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="label" stroke="#64748b" tick={{ fontSize: 11 }} />
        <YAxis stroke="#64748b" tick={{ fontSize: 11 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
        <Tooltip
          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 6 }}
          labelStyle={{ color: '#94a3b8' }}
          formatter={(value: number) => [formatCurrency(value), 'Equity']}
        />
        <Area type="monotone" dataKey="equity" stroke="#3b82f6" fill="url(#equityGrad)" strokeWidth={2} dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  )
}
