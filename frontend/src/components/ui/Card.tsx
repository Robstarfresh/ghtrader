import { cn } from '@/lib/utils'

export function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('bg-surface border border-border rounded-lg p-4', className)}>
      {children}
    </div>
  )
}

export function CardHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-4">
      <h3 className="text-sm font-semibold text-muted uppercase tracking-wider">{title}</h3>
      {subtitle && <p className="text-xs text-muted mt-1">{subtitle}</p>}
    </div>
  )
}
