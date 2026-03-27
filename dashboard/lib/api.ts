import axios from 'axios'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: API, timeout: 15000 })

export const botApi = {
  status:    () => api.get('/status'),
  start:     () => api.post('/bot/start'),
  stop:      () => api.post('/bot/stop'),
  portfolio: () => api.get('/portfolio'),
  positions: () => api.get('/positions'),
  signals:   () => api.get('/signals'),
  scan:      (symbols: string[]) => api.post('/scan', { symbols }),
  skills:    () => api.get('/skills'),
  ticker:    (symbol: string) => api.get(`/ticker/${symbol}`),
  authStatus:() => api.get('/auth/status'),
  authStart: (provider: string, returnUrl: string) => api.post('/auth/start', { provider, return_url: returnUrl }),
  setTelegram:(token: string, chatId: string) => api.post('/telegram/config', { token, chat_id: chatId }),
  setBinance: (key: string, secret: string) => api.post('/binance/config', { api_key: key, secret_key: secret }),
  buy:       (symbol: string, qty: number) => api.post('/order/buy', { symbol, qty }),
  sell:      (symbol: string, qty: number) => api.post('/order/sell', { symbol, qty }),
  close:     (symbol: string) => api.post(`/position/close/${symbol}`),
  aiChat:    (msg: string) => api.post('/ai/chat', { message: msg }),
  history:   () => api.get('/trades/history'),
  connectStatus: () => axios.get('/api/connect/status'),
}
