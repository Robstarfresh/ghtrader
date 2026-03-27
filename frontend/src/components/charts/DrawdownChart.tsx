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

interface DataPoint {
  timestamp: string
  equity: number
}

interface DrawdownChartProps {
  data: DataPoint[]
  loading?: boolean
}

export function DrawdownChart({ data, loading }: DrawdownChartProps) {
  if (loading) return <div className="h-48 animate-pulse bg-border rounded" />

  if (!data || data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-muted text-sm">
        No drawdown data yet
      </div>
    )
  }

  let peak = data[0]?.equity ?? 0
  const formatted = data.map((d) => {
    if (d.equity > peak) peak = d.equity
    const dd = peak > 0 ? ((d.equity - peak) / peak) * 100 : 0
    return {
      label: new Date(d.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      drawdown: parseFloat(dd.toFixed(2)),
    }
  })

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={formatted}>
        <defs>
          <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="label" stroke="#64748b" tick={{ fontSize: 11 }} />
        <YAxis stroke="#64748b" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
        <Tooltip
          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 6 }}
          labelStyle={{ color: '#94a3b8' }}
          formatter={(value: number) => [`${value}%`, 'Drawdown']}
        />
        <Area type="monotone" dataKey="drawdown" stroke="#ef4444" fill="url(#ddGrad)" strokeWidth={2} dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  )
}
