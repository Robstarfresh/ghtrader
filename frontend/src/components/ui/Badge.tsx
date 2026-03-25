import { cn } from '@/lib/utils'

type BadgeVariant = 'success' | 'danger' | 'warning' | 'info' | 'muted'

export function Badge({
  children,
  variant = 'info',
}: {
  children: React.ReactNode
  variant?: BadgeVariant
}) {
  const styles: Record<BadgeVariant, string> = {
    success: 'bg-green-500/20 text-green-400 border border-green-500/30',
    danger: 'bg-red-500/20 text-red-400 border border-red-500/30',
    warning: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
    info: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
    muted: 'bg-slate-500/20 text-slate-400 border border-slate-500/30',
  }
  return (
    <span className={cn('px-2 py-0.5 rounded text-xs font-medium', styles[variant])}>
      {children}
    </span>
  )
}
