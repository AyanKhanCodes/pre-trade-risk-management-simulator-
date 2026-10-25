import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { PortfolioSummary, Position } from '../../types';
import { Wallet, Briefcase, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';

export const PortfolioView: React.FC = () => {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadPortfolio = async () => {
    setLoading(true);
    try {
      const [sumRes, posRes] = await Promise.all([
        api.getPortfolioSummary(),
        api.getPortfolioPositions(),
      ]);
      setSummary(sumRes);
      setPositions(posRes || []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPortfolio();
  }, []);

  const totalPnl = summary ? parseFloat(summary.total_unrealized_pnl) : 0;
  const isPnlPositive = totalPnl >= 0;

  return (
    <div className="space-y-6">
      {/* Portfolio Header Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Cash Balance */}
        <div className="bg-[#0b101b] border border-slate-800 rounded-2xl p-5 shadow-xl flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Simulated Cash
            </div>
            <div className="text-2xl font-mono font-bold text-white mt-1">
              ₹{summary ? parseFloat(summary.cash_balance).toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '10,00,000.00'}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Available for simulated orders</div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-indigo-950/60 border border-indigo-800/40 flex items-center justify-center text-indigo-400">
            <Wallet className="w-6 h-6" />
          </div>
        </div>

        {/* Portfolio Valuation */}
        <div className="bg-[#0b101b] border border-slate-800 rounded-2xl p-5 shadow-xl flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Total Portfolio Value
            </div>
            <div className="text-2xl font-mono font-bold text-white mt-1">
              ₹{summary ? parseFloat(summary.portfolio_value).toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '10,00,000.00'}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Cash + open position market value</div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-300">
            <Briefcase className="w-6 h-6" />
          </div>
        </div>

        {/* Unrealized P&L */}
        <div className="bg-[#0b101b] border border-slate-800 rounded-2xl p-5 shadow-xl flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Unrealized P&L
            </div>
            <div
              className={`text-2xl font-mono font-bold mt-1 ${
                isPnlPositive ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {isPnlPositive ? '+' : ''}₹{Math.abs(totalPnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Mark-to-market simulated gain/loss</div>
          </div>
          <div
            className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              isPnlPositive
                ? 'bg-emerald-950/60 border border-emerald-800/40 text-emerald-400'
                : 'bg-rose-950/60 border border-rose-800/40 text-rose-400'
            }`}
          >
            {isPnlPositive ? <TrendingUp className="w-6 h-6" /> : <TrendingDown className="w-6 h-6" />}
          </div>
        </div>
      </div>

      {/* Positions Table */}
      <div className="bg-[#0b101b] border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide uppercase">Open Equity Positions</h3>
            <p className="text-xs text-slate-400">Positions settled upon simulated execution approval.</p>
          </div>
          <button
            onClick={loadPortfolio}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-mono uppercase text-[11px] border-b border-slate-800">
              <tr>
                <th className="px-5 py-3">Symbol</th>
                <th className="px-5 py-3 text-right">Quantity</th>
                <th className="px-5 py-3 text-right">Avg Entry (₹)</th>
                <th className="px-5 py-3 text-right">LTP (₹)</th>
                <th className="px-5 py-3 text-right">Market Value (₹)</th>
                <th className="px-5 py-3 text-right">Unrealized P&L</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {positions.map((p) => {
                const pnl = parseFloat(p.unrealized_pnl);
                const isPosPnl = pnl >= 0;

                return (
                  <tr key={p.symbol} className="hover:bg-slate-900/40 transition-colors">
                    <td className="px-5 py-3.5 font-bold text-white text-sm">
                      {p.symbol}
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono text-slate-200">
                      {p.quantity}
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono text-slate-300">
                      ₹{parseFloat(p.average_entry_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono text-slate-200">
                      ₹{parseFloat(p.current_market_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono font-bold text-white">
                      ₹{parseFloat(p.market_value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono font-bold">
                      <span className={isPosPnl ? 'text-emerald-400' : 'text-rose-400'}>
                        {isPosPnl ? '+' : ''}₹{pnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })} ({p.unrealized_pnl_pct}%)
                      </span>
                    </td>
                  </tr>
                );
              })}
              {positions.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-slate-500 text-xs">
                    No open positions. Submit and execute simulated buy orders to build a portfolio.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
