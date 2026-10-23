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
};
