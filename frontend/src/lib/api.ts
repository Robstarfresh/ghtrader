import axios from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 10000,
})

export const healthApi = {
  getHealth: () => api.get('/api/v1/health'),
}

export const marketDataApi = {
  getPairs: () => api.get('/api/v1/pairs'),
  getCandles: (pair: string, timeframe = '1m', limit = 100) =>
    api.get(`/api/v1/candles/${encodeURIComponent(pair)}`, { params: { timeframe, limit } }),
}

export const engineApi = {
  getStatus: () => api.get('/api/v1/engine/status'),
  start: () => api.post('/api/v1/engine/start'),
  stop: () => api.post('/api/v1/engine/stop'),
}

export const positionsApi = {
  getOpen: () => api.get('/api/v1/positions'),
  getHistory: () => api.get('/api/v1/positions/history'),
}

export const tradesApi = {
  getRecent: (limit = 50, offset = 0) => api.get('/api/v1/trades', { params: { limit, offset } }),
}

export const pnlApi = {
  getSummary: () => api.get('/api/v1/pnl/summary'),
  getEquityCurve: () => api.get('/api/v1/pnl/equity-curve'),
}

export const backtestApi = {
  run: (config: BacktestConfig) => api.post('/api/v1/backtests', config),
  list: () => api.get('/api/v1/backtests'),
  get: (id: number) => api.get(`/api/v1/backtests/${id}`),
  getTrades: (id: number) => api.get(`/api/v1/backtests/${id}/trades`),
  getLeaderboard: () => api.get('/api/v1/backtests/leaderboard'),
}

export const riskApi = {
  getStatus: () => api.get('/api/v1/risk/status'),
  reset: () => api.post('/api/v1/risk/reset'),
}

export const strategiesApi = {
  list: () => api.get('/api/v1/strategies'),
  create: (data: StrategyData) => api.post('/api/v1/strategies', data),
  update: (id: number, data: Partial<StrategyData>) => api.patch(`/api/v1/strategies/${id}`, data),
}

export interface BacktestConfig {
  name: string
  strategy_name: string
  pair: string
  timeframe: string
  start_date: string
  end_date: string
  initial_balance?: number
  config?: Record<string, unknown>
}

export interface StrategyData {
  name: string
  description?: string
  params?: Record<string, unknown>
  is_active?: boolean
}

export default api
