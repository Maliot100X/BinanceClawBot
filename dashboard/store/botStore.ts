import { create } from 'zustand'
import { botApi } from '@/lib/api'

interface BotState {
  isRunning: boolean
  status: any
  portfolio: any
  positions: any[]
  signals: any[]
  skills: string[]
  authStatus: Record<string, boolean>
  loading: boolean
  error: string | null
  // Actions
  fetchStatus: () => Promise<void>
  fetchPortfolio: () => Promise<void>
  fetchPositions: () => Promise<void>
  fetchSignals: () => Promise<void>
  fetchAuth: () => Promise<void>
  startBot: () => Promise<void>
  stopBot: () => Promise<void>
  sendBuy: (symbol: string, qty: number) => Promise<any>
  sendSell: (symbol: string, qty: number) => Promise<any>
  closePosition: (symbol: string) => Promise<any>
  chatWithAI: (msg: string) => Promise<string>
  setTelegramConfig: (token: string, chatId: string) => Promise<void>
  setBinanceConfig: (key: string, secret: string) => Promise<void>
}

export const useBotStore = create<BotState>((set, get) => ({
  isRunning: false,
  status: null,
  portfolio: null,
  positions: [],
  signals: [],
  skills: [],
  authStatus: {},
  loading: false,
  error: null,

  fetchStatus: async () => {
    try {
      const r = await botApi.status()
      set({ status: r.data, isRunning: r.data?.running === true, error: null })
    } catch { set({ error: 'Backend offline - start main.py first' }) }
  },

  fetchPortfolio: async () => {
    try { const r = await botApi.portfolio(); set({ portfolio: r.data }) } catch {}
  },

  fetchPositions: async () => {
    try { const r = await botApi.positions(); set({ positions: r.data?.positions || [] }) } catch {}
  },

  fetchSignals: async () => {
    try { const r = await botApi.signals(); set({ signals: r.data?.signals || [] }) } catch {}
  },

  fetchAuth: async () => {
    try { const r = await botApi.authStatus(); set({ authStatus: r.data || {} }) } catch {}
  },

  startBot: async () => {
    await botApi.start(); set({ isRunning: true })
  },

  stopBot: async () => {
    await botApi.stop(); set({ isRunning: false })
  },

  sendBuy: async (symbol, qty) => {
    const r = await botApi.buy(symbol, qty); return r.data
  },

  sendSell: async (symbol, qty) => {
    const r = await botApi.sell(symbol, qty); return r.data
  },

  closePosition: async (symbol) => {
    const r = await botApi.close(symbol); return r.data
  },

  chatWithAI: async (msg) => {
    try { const r = await botApi.aiChat(msg); return r.data?.reply || 'No response' }
    catch { return 'AI unavailable — check OAuth authentication' }
  },

  setTelegramConfig: async (token, chatId) => {
    await botApi.setTelegram(token, chatId)
  },

  setBinanceConfig: async (key, secret) => {
    await botApi.setBinance(key, secret)
  },
}))
