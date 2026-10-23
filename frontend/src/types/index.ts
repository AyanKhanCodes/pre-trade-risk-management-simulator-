export type OrderSide = 'BUY' | 'SELL';

export type OrderStatus = 'CREATED' | 'VALIDATING' | 'APPROVED' | 'REJECTED' | 'EXECUTED';

export interface RiskCheck {
  rule_id: string;
  rule_name: string;
  passed: boolean;
  reason: string;
}

export interface Order {
  order_id: string;
  symbol: string;
  side: OrderSide;
  quantity: number;
  price: string;
  order_value: string;
  status: OrderStatus;
  rejection_reasons: string[];
  risk_checks: RiskCheck[];
  created_at: string;
}

export interface OrderCreateRequest {
  symbol: string;
  side: OrderSide;
  quantity: number;
  price: string;
}

export interface OrderListResponse {
  orders: Order[];
  total: number;
}

export interface RiskConfig {
  max_order_value: string;
  restricted_symbols: string[];
  min_price: string;
  max_quantity: number;
  max_price: string;
  max_daily_orders: number;
  max_daily_notional: string;
}

export interface RiskConfigUpdateRequest {
  max_order_value?: string;
  restricted_symbols?: string[];
  min_price?: string;
  max_quantity?: number;
  max_price?: string;
  max_daily_orders?: number;
  max_daily_notional?: string;
}

export interface RiskRule {
  rule_id: string;
  name: string;
  description: string;
  category: string;
  config_key: string;
  current_value: string | null;
  enabled: boolean;
}

export interface RiskRulesListResponse {
  rules: RiskRule[];
}

export interface DailyStats {
  total_orders: number;
  approved: number;
  rejected: number;
  approval_rate: number;
  total_notional: string;
}

export interface TopSymbolStat {
  symbol: string;
  count: number;
}

export interface OrderStatsSummary {
  today: DailyStats;
  all_time: DailyStats;
  top_symbols: TopSymbolStat[];
}
