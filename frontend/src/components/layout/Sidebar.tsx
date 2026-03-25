'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  TrendingUp,
  History,
  FlaskConical,
  Sliders,
  ShieldAlert,
  Settings,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/positions', label: 'Positions', icon: TrendingUp },
  { href: '/trades', label: 'Trades', icon: History },
  { href: '/backtests', label: 'Backtests', icon: FlaskConical },
  { href: '/strategies', label: 'Strategies', icon: Sliders },
  { href: '/risk', label: 'Risk', icon: ShieldAlert },
  { href: '/settings', label: 'Settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-56 min-h-screen bg-surface border-r border-border flex flex-col">
      <div className="p-4 border-b border-border">
        <h1 className="text-lg font-bold text-white">GHTrader</h1>
        <span className="inline-block mt-1 px-2 py-0.5 rounded text-xs font-bold bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
          PAPER TRADING
        </span>
      </div>
      <nav className="flex-1 py-4">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              'flex items-center gap-3 px-4 py-2.5 text-sm transition-colors',
              pathname === href
                ? 'bg-primary/20 text-primary border-r-2 border-primary'
                : 'text-muted hover:text-white hover:bg-white/5'
            )}
          >
            <Icon size={16} />
            {label}
          </Link>
        ))}
      </nav>
      <div className="p-4 border-t border-border">
        <p className="text-xs text-muted">⚠️ Simulation only</p>
        <p className="text-xs text-muted">No real orders placed</p>
      </div>
    </aside>
  )
}
