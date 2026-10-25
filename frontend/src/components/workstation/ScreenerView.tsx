import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { ScreenerStockResult } from '../../types';
import { Filter, Search, ArrowUpRight, ShieldCheck, ShieldAlert, RefreshCw } from 'lucide-react';

interface ScreenerViewProps {
  onTradeSymbol: (symbol: string, price: string) => void;
}

export const ScreenerView: React.FC<ScreenerViewProps> = ({ onTradeSymbol }) => {
  const [results, setResults] = useState<ScreenerStockResult[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [minPrice, setMinPrice] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<string>('');
  const [eligibleOnly, setEligibleOnly] = useState<boolean>(false);

  const fetchResults = async () => {
    setLoading(true);
    try {
      const res = await api.getScreenerResults({
        min_price: minPrice ? parseFloat(minPrice) : undefined,
        max_price: maxPrice ? parseFloat(maxPrice) : undefined,
      });
      setResults(res.results || []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, [minPrice, maxPrice]);

  const filtered = results.filter((r) => {
    if (searchTerm && !r.symbol.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !r.company_name.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    if (eligibleOnly && !r.preliminary_eligible) {
      return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header & Filter Card */}
      <div className="bg-[#0b101b] border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              <Filter className="w-5 h-5 text-indigo-400" />
              NSE Cash Equity Stock Screener
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Screen entitled Indian equities with preliminary pre-trade risk eligibility checks.
            </p>
          </div>

          <button
            onClick={fetchResults}
            disabled={loading}
            className="px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-700 hover:border-slate-500 text-xs font-semibold text-slate-200 flex items-center gap-2 self-start md:self-auto transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh Screener
          </button>
        </div>

        {/* Filter Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search symbol or company..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="number"
              placeholder="Min Price (₹)"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
            <input
              type="number"
              placeholder="Max Price (₹)"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300">
              <input
                type="checkbox"
                checked={eligibleOnly}
                onChange={(e) => setEligibleOnly(e.target.checked)}
                className="w-4 h-4 rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-0"
              />
              Show Eligible Only
            </label>
          </div>

          <div className="text-right flex items-center justify-end text-xs text-slate-400 font-mono">
            Matches: {filtered.length} / {results.length}
          </div>
        </div>
      </div>

      {/* Results Table */}
      <div className="bg-[#0b101b] border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-mono uppercase text-[11px] border-b border-slate-800">
              <tr>
                <th className="px-5 py-3">Symbol / Company</th>
                <th className="px-5 py-3 text-right">LTP (₹)</th>
                <th className="px-5 py-3 text-right">Day Change</th>
                <th className="px-5 py-3 text-right">Volume</th>
                <th className="px-5 py-3">Preliminary Risk Status</th>
                <th className="px-5 py-3 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {filtered.map((stock) => {
                const isUp = parseFloat(stock.change) >= 0;

                return (
                  <tr key={stock.security_id} className="hover:bg-slate-900/50 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="font-bold text-white text-sm">{stock.symbol}</div>
                      <div className="text-[11px] text-slate-400 truncate max-w-xs">
                        {stock.company_name}
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono font-bold text-slate-100">
                      ₹{parseFloat(stock.ltp).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono font-semibold">
                      <span className={isUp ? 'text-emerald-400' : 'text-rose-400'}>
                        {isUp ? '+' : ''}
                        {stock.change} ({stock.change_pct}%)
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono text-slate-300">
                      {stock.volume.toLocaleString('en-IN')}
                    </td>
                    <td className="px-5 py-3.5">
                      {stock.preliminary_eligible ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
                          <ShieldCheck className="w-3.5 h-3.5" />
                          Eligible
                        </span>
                      ) : (
                        <div className="space-y-1">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-950/80 text-rose-400 border border-rose-800/60">
                            <ShieldAlert className="w-3.5 h-3.5" />
                            Flagged
                          </span>
                          <div className="text-[10px] text-rose-300">
                            {stock.risk_flags.join(', ')}
                          </div>
                        </div>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-center">
                      <button
                        onClick={() => onTradeSymbol(stock.symbol, stock.ltp)}
                        className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center gap-1 mx-auto transition-all shadow-sm"
                      >
                        Trade
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-slate-500 text-xs">
                    No instruments match the selected filter criteria.
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
