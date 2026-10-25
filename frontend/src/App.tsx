import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar, NavTab } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { OrderForm } from './components/order-entry/OrderForm';
import { LiveValidationCard } from './components/order-entry/LiveValidationCard';
import { OrderResultBanner } from './components/order-entry/OrderResultBanner';
import { OrderHistoryTable } from './components/order-history/OrderHistoryTable';
import { RiskRuleCard } from './components/risk-rules/RiskRuleCard';
import { RulesPipelineVisual } from './components/risk-rules/RulesPipelineVisual';
import { StatsKPIs } from './components/analytics/StatsKPIs';
import { ApprovalRateChart } from './components/analytics/ApprovalRateChart';
import { RejectionPieChart } from './components/analytics/RejectionPieChart';
import { TopSymbolsCard } from './components/analytics/TopSymbolsCard';
import { TradingViewChart } from './components/workstation/TradingViewChart';
import { Watchlist } from './components/workstation/Watchlist';
import { ScreenerView } from './components/workstation/ScreenerView';
import { PortfolioView } from './components/workstation/PortfolioView';
import { api } from './lib/api';
import {
  Candle,
  FeedHealth,
  Order,
  OrderCreateRequest,
  OrderSide,
  OrderStatsSummary,
  Quote,
  RiskConfig,
  RiskConfigUpdateRequest,
  RiskRule,
} from './types';
import { Sliders, AlertTriangle } from 'lucide-react';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('workstation');

  // Application Data States
  const [orders, setOrders] = useState<Order[]>([]);
  const [config, setConfig] = useState<RiskConfig | null>(null);
  const [rules, setRules] = useState<RiskRule[]>([]);
  const [stats, setStats] = useState<OrderStatsSummary | null>(null);

  // Market Workstation Data States
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('RELIANCE');
  const [candles, setCandles] = useState<Candle[]>([]);
  const [chartInterval, setChartInterval] = useState<string>('1m');
  const [feedHealth, setFeedHealth] = useState<FeedHealth | null>(null);

  // Cross-module Trade Transfer State
  const [tradeSymbol, setTradeSymbol] = useState<string>('RELIANCE');
  const [tradePrice, setTradePrice] = useState<string>('2945.50');

  // Interaction States
  const [lastOrder, setLastOrder] = useState<Order | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [globalError, setGlobalError] = useState<string | null>(null);

  // Live validation sync values from OrderForm
  const [formValues, setFormValues] = useState<{
    symbol: string;
    side: OrderSide;
    quantity: number | '';
    price: string;
  }>({
    symbol: 'RELIANCE',
    side: 'BUY',
    quantity: 10,
    price: '2945.50',
  });

  // Load initial data
  const loadAllData = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) setIsRefreshing(true);
    setGlobalError(null);
    try {
      const [ordersRes, configRes, rulesRes, statsRes, quotesRes, healthRes] =
        await Promise.all([
          api.listOrders(),
          api.getRiskConfig(),
          api.getRiskRules(),
          api.getOrderStats(),
          api.getMarketQuotes().catch(() => []),
          api.getMarketStatus().catch(() => null),
        ]);

      setOrders(ordersRes.orders || []);
      setConfig(configRes);
      setRules(rulesRes.rules || []);
      setStats(statsRes);
      setQuotes(quotesRes);
      setFeedHealth(healthRes);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setGlobalError(`Failed to sync with backend: ${err.message}`);
      } else {
        setGlobalError('Unable to connect to FastAPI risk engine.');
      }
    } finally {
      setIsLoading(false);
      if (showRefreshing) setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadAllData();
    const interval = setInterval(() => {
      loadAllData();
    }, 12000);
    return () => clearInterval(interval);
  }, [loadAllData]);

  // Load chart candles when selectedSymbol or chartInterval changes
  useEffect(() => {
    let isMounted = true;
    api.getMarketCandles(selectedSymbol, chartInterval, 100)
      .then((c) => {
        if (isMounted) setCandles(c);
      })
      .catch(() => {});
    return () => {
      isMounted = false;
    };
  }, [selectedSymbol, chartInterval]);

  // Connect to live WebSocket feed
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/market`;
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;

    const connectWs = () => {
      try {
        ws = new WebSocket(wsUrl);
        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'QUOTE' && msg.data) {
              const newQuote: Quote = msg.data;
              setQuotes((prev) =>
                prev.map((q) => (q.symbol === newQuote.symbol ? newQuote : q))
              );
            }
          } catch {
            // ignore
          }
        };
        ws.onclose = () => {
          reconnectTimer = setTimeout(connectWs, 3000);
        };
        ws.onerror = () => {
          ws?.close();
        };
      } catch {
        reconnectTimer = setTimeout(connectWs, 3000);
      }
    };

    connectWs();
    return () => {
      if (ws) ws.close();
      clearTimeout(reconnectTimer);
    };
  }, []);

  // Order Submission Handler
  const handleOrderSubmit = async (req: OrderCreateRequest) => {
    setIsSubmitting(true);
    try {
      const created = await api.createOrder(req);
      setLastOrder(created);
      setOrders((prev) => [created, ...prev]);
      try {
        const newStats = await api.getOrderStats();
        setStats(newStats);
      } catch {
        // silent
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Simulated Execution Handler
  const handleExecuteOrder = async (orderId: string) => {
    try {
      const executed = await api.executeOrder(orderId);
      setLastOrder(executed);
      setOrders((prev) =>
        prev.map((o) => (o.order_id === orderId ? executed : o))
      );
      const newStats = await api.getOrderStats();
      setStats(newStats);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setGlobalError(`Execution failed: ${err.message}`);
      }
    }
  };

  // Rule Configuration Update Handler
  const handleConfigUpdate = async (updates: RiskConfigUpdateRequest) => {
    const updated = await api.updateRiskConfig(updates);
    setConfig(updated);
    const rulesRes = await api.getRiskRules();
    setRules(rulesRes.rules);
  };

  // Quick trade from Watchlist or Screener
  const handleTradeSymbol = (sym: string, price: string) => {
    setTradeSymbol(sym);
    setTradePrice(price);
    setCurrentTab('trade');
  };

  const currentQuote = quotes.find((q) => q.symbol === selectedSymbol) || null;

  return (
    <div className="flex flex-col lg:flex-row min-h-screen bg-[#080c14] text-slate-100">
      {/* Sidebar Navigation */}
      <Sidebar
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        config={config}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          onRefresh={() => loadAllData(true)}
          isRefreshing={isRefreshing}
        />

        <main className="p-4 sm:p-6 lg:p-8 space-y-6 flex-1 overflow-y-auto">
          {globalError && (
            <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-800/80 text-rose-300 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{globalError}</span>
              </div>
              <button
                onClick={() => loadAllData(true)}
                className="px-2.5 py-1 rounded bg-rose-900/60 hover:bg-rose-800 text-white font-medium"
              >
                Retry Connection
              </button>
            </div>
          )}

          {/* TAB 0: MARKET WORKSTATION */}
          {currentTab === 'workstation' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                <div className="lg:col-span-8">
                  <TradingViewChart
                    symbol={selectedSymbol}
                    candles={candles}
                    latestQuote={currentQuote}
                    interval={chartInterval}
                    onIntervalChange={setChartInterval}
                  />
                </div>

                <div className="lg:col-span-4">
                  <Watchlist
                    quotes={quotes}
                    selectedSymbol={selectedSymbol}
                    onSelectSymbol={setSelectedSymbol}
                    onTradeSymbol={handleTradeSymbol}
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 1: STOCK SCREENER */}
          {currentTab === 'screener' && (
            <ScreenerView onTradeSymbol={handleTradeSymbol} />
          )}

          {/* TAB 2: SIMULATED PORTFOLIO */}
          {currentTab === 'portfolio' && <PortfolioView />}

          {/* TAB 3: ORDER EXECUTION */}
          {currentTab === 'trade' && (
            <div className="space-y-6">
              {/* Order Result Banner with simulated execution button */}
              {lastOrder && (
                <OrderResultBanner
                  order={lastOrder}
                  onDismiss={() => setLastOrder(null)}
                  onExecute={handleExecuteOrder}
                />
              )}

              {/* Order Terminal Split View */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                <div className="lg:col-span-6">
                  <OrderForm
                    onSubmit={handleOrderSubmit}
                    isLoading={isSubmitting}
                    config={config}
                    onValuesChange={setFormValues}
                    initialSymbol={tradeSymbol}
                    initialPrice={tradePrice}
                  />
                </div>

                <div className="lg:col-span-6">
                  <LiveValidationCard
                    symbol={formValues.symbol}
                    quantity={formValues.quantity}
                    price={formValues.price}
                    config={config}
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: ORDER AUDIT HISTORY */}
          {currentTab === 'orders' && (
            <OrderHistoryTable
              orders={orders}
              isLoading={isLoading}
              onRefresh={() => loadAllData(true)}
            />
          )}

          {/* TAB 5: RISK RULES ENGINE */}
          {currentTab === 'rules' && (
            <div className="space-y-6">
              <div className="rounded-2xl bg-[#0f1626] border border-slate-800 p-5 shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                    <Sliders className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-100 tracking-tight">
                      Configurable Pre-Trade Risk Rules
                    </h2>
                    <p className="text-xs text-slate-400">
                      Real-time parameters governing position limits, microcaps, and regulatory compliance
                    </p>
                  </div>
                </div>

                <div className="text-xs font-mono px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300">
                  9 Active Risk Gates
                </div>
              </div>

              {/* Grid of 9 Risk Rules */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {rules.map((rule) => (
                  <RiskRuleCard
                    key={rule.rule_id}
                    rule={rule}
                    onUpdateConfig={handleConfigUpdate}
                  />
                ))}
              </div>

              {/* Architectural Pipeline Explainer */}
              <RulesPipelineVisual />
            </div>
          )}

          {/* TAB 6: RISK ANALYTICS */}
          {currentTab === 'analytics' && (
            <div className="space-y-6">
              {/* KPIs Header */}
              <StatsKPIs stats={stats} config={config} />

              {/* Chart Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ApprovalRateChart stats={stats} />
                <RejectionPieChart stats={stats} />
              </div>

              {/* Top Symbols */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-1">
                  <TopSymbolsCard symbols={stats?.top_symbols || []} />
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
