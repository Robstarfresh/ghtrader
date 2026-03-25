import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f172a',
        surface: '#1e293b',
        border: '#334155',
        primary: '#3b82f6',
        success: '#22c55e',
        danger: '#ef4444',
        warning: '#f59e0b',
        muted: '#64748b',
      },
    },
  },
  plugins: [],
}
export default config
