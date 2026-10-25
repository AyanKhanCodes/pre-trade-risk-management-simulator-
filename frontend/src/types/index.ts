export type OrderSide = 'BUY' | 'SELL';

export type OrderStatus = 'CREATED' | 'VALIDATING' | 'APPROVED' | 'REJECTED' | 'EXECUTED';

export interface RiskCheck {
  rule_id: string;
  rule_name: string;
  passed: boolean;
  reason: string;
  status?: string;
  applicable_side?: string;
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
  currency?: string;
}

export interface OrderCreateRequest {
  symbol: string;
  side: OrderSide;
  quantity: number;
  price: string;
  currency?: string;
}

export interface OrderPreviewResponse {
  symbol: string;
  side: string;
  quantity: number;
  price: string;
  order_value: string;
  currency: string;
  passed: boolean;
  rejection_reasons: string[];
  risk_checks: RiskCheck[];
  daily_order_count: number;
  daily_notional: string;
  held_quantity?: number;
  reserved_quantity?: number;
  sellable_quantity?: number;
  preview_timestamp: string;
}

export interface Instrument {
  security_id: string;
  trading_symbol: string;
  exchange_segment: string;
  company_name: string;
  isin: string;
  lot_size: number;
  tick_size: string;
  currency: string;
}

export interface Quote {
  security_id: string;
  symbol: string;
  ltp: string;
  open: string;
  high: string;
  low: string;
  close: string;
  change: string;
  change_pct: string;
  volume: number;
  timestamp: string;
  feed_status: 'LIVE' | 'STALE' | 'DISCONNECTED' | 'MARKET_CLOSED';
}

export interface Candle {
  timestamp: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: number;
}

export interface FeedHealth {
  status: 'LIVE' | 'STALE' | 'DISCONNECTED' | 'MARKET_CLOSED';
  provider: string;
  subscribed_symbols_count: number;
  last_heartbeat_utc: string;
  latency_ms: number;
  mode: string;
}

export interface ScreenerStockResult {
  security_id: string;
  symbol: string;
  company_name: string;
  ltp: string;
  change: string;
  change_pct: string;
  volume: number;
  feed_status: string;
  timestamp: string;
  preliminary_eligible: boolean;
  risk_flags: string[];
}

export interface ScreenerResponse {
  total_screened: number;
  matches_count: number;
  results: ScreenerStockResult[];
}

export interface Position {
  symbol: string;
  quantity: number;
  reserved_quantity?: number;
  sellable_quantity?: number;
  average_entry_price: string;
  current_market_price: string;
  market_value: string;
  unrealized_pnl: string;
  unrealized_pnl_pct: string;
  updated_at: string;
}

export interface PositionDetailResponse {
  symbol: string;
  held_qty: number;
  reserved_qty: number;
  sellable_qty: number;
  average_entry_price?: string;
  current_market_price?: string;
  unrealized_pnl?: string;
}

export interface PortfolioSummary {
  account_id: string;
  currency: string;
  cash_balance: string;
  portfolio_value: string;
  total_unrealized_pnl: string;
  open_positions_count: number;
  updated_at: string;
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
  applicable_side?: string;
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
