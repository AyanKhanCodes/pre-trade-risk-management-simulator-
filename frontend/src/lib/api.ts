import {
  Order,
  OrderCreateRequest,
  OrderListResponse,
  OrderStatsSummary,
  RiskConfig,
  RiskConfigUpdateRequest,
  RiskRulesListResponse,
} from '../types';

const API_BASE = '/api';

class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetails: unknown;
    let message = `Request failed with status ${res.status}`;
    try {
      const data = await res.json();
      errorDetails = data;
      if (typeof data.detail === 'string') {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map((d: { msg?: string }) => d.msg || 'Validation error').join(', ');
      }
    } catch {
      // Body is not json
    }
    throw new ApiError(message, res.status, errorDetails);
  }
  return res.json() as Promise<T>;
}

export const api = {
  async createOrder(order: OrderCreateRequest): Promise<Order> {
    const res = await fetch(`${API_BASE}/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(order),
    });
    return handleResponse<Order>(res);
  },

  async listOrders(): Promise<OrderListResponse> {
    const res = await fetch(`${API_BASE}/orders`);
    return handleResponse<OrderListResponse>(res);
  },

  async getOrder(orderId: string): Promise<Order> {
    const res = await fetch(`${API_BASE}/orders/${encodeURIComponent(orderId)}`);
    return handleResponse<Order>(res);
  },

  async getRiskConfig(): Promise<RiskConfig> {
    const res = await fetch(`${API_BASE}/risk-config`);
    return handleResponse<RiskConfig>(res);
  },

  async updateRiskConfig(updates: RiskConfigUpdateRequest): Promise<RiskConfig> {
    const res = await fetch(`${API_BASE}/risk-config`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    return handleResponse<RiskConfig>(res);
  },

  async getRiskRules(): Promise<RiskRulesListResponse> {
    const res = await fetch(`${API_BASE}/risk-rules`);
    return handleResponse<RiskRulesListResponse>(res);
  },

  async getOrderStats(): Promise<OrderStatsSummary> {
    const res = await fetch(`${API_BASE}/orders/stats/summary`);
    return handleResponse<OrderStatsSummary>(res);
  },

  async checkHealth(): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<{ status: string }>(res);
  },

  async executeOrder(orderId: string): Promise<Order> {
    const res = await fetch(`${API_BASE}/orders/${encodeURIComponent(orderId)}/execute`, {
      method: 'POST',
    });
    return handleResponse<Order>(res);
  },

  async previewOrder(order: OrderCreateRequest): Promise<import('../types').OrderPreviewResponse> {
    const res = await fetch(`${API_BASE}/orders/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(order),
    });
    return handleResponse<import('../types').OrderPreviewResponse>(res);
  },

  async getMarketStatus(): Promise<import('../types').FeedHealth> {
    const res = await fetch(`${API_BASE}/market/status`);
    return handleResponse<import('../types').FeedHealth>(res);
  },

  async getMarketInstruments(): Promise<import('../types').Instrument[]> {
    const res = await fetch(`${API_BASE}/market/instruments`);
    return handleResponse<import('../types').Instrument[]>(res);
  },

  async getMarketQuotes(): Promise<import('../types').Quote[]> {
    const res = await fetch(`${API_BASE}/market/quotes`);
    return handleResponse<import('../types').Quote[]>(res);
  },

  async getMarketQuote(symbol: string): Promise<import('../types').Quote> {
    const res = await fetch(`${API_BASE}/market/quotes/${encodeURIComponent(symbol)}`);
    return handleResponse<import('../types').Quote>(res);
  },

  async getMarketCandles(
    symbol: string,
    interval: string = '1m',
    limit: number = 100
  ): Promise<import('../types').Candle[]> {
    const res = await fetch(
      `${API_BASE}/market/candles?symbol=${encodeURIComponent(symbol)}&interval=${interval}&limit=${limit}`
    );
    return handleResponse<import('../types').Candle[]>(res);
  },

  async getScreenerResults(params?: {
    min_price?: number;
    max_price?: number;
    min_volume?: number;
    min_change_pct?: number;
    max_change_pct?: number;
  }): Promise<import('../types').ScreenerResponse> {
    const q = new URLSearchParams();
    if (params?.min_price) q.append('min_price', params.min_price.toString());
    if (params?.max_price) q.append('max_price', params.max_price.toString());
    if (params?.min_volume) q.append('min_volume', params.min_volume.toString());
    if (params?.min_change_pct) q.append('min_change_pct', params.min_change_pct.toString());
    if (params?.max_change_pct) q.append('max_change_pct', params.max_change_pct.toString());
    const res = await fetch(`${API_BASE}/screener?${q.toString()}`);
    return handleResponse<import('../types').ScreenerResponse>(res);
  },

  async getPortfolioSummary(): Promise<import('../types').PortfolioSummary> {
    const res = await fetch(`${API_BASE}/portfolio/summary`);
    return handleResponse<import('../types').PortfolioSummary>(res);
  },

  async getPortfolioPositions(): Promise<import('../types').Position[]> {
    const res = await fetch(`${API_BASE}/portfolio/positions`);
    return handleResponse<import('../types').Position[]>(res);
  },
};
