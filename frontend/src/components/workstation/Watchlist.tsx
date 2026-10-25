import React from 'react';
import { Quote } from '../../types';
import { TrendingUp, TrendingDown, ArrowUpRight } from 'lucide-react';

interface WatchlistProps {
  quotes: Quote[];
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  onTradeSymbol: (symbol: string, price: string) => void;
}

export const Watchlist: React.FC<WatchlistProps> = ({
  quotes,
  selectedSymbol,
  onSelectSymbol,
  onTradeSymbol,
}) => {
  return (
    <div className="bg-[#0b101b] border border-slate-800 rounded-2xl p-4 shadow-xl flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 mb-2 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide uppercase">Watchlist</h3>
          <p className="text-xs text-slate-400">Top 20 NSE Cash Equities</p>
        </div>
        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
          {quotes.length} tickers
        </span>
      </div>

      <div className="overflow-y-auto space-y-1.5 flex-1 max-h-[460px] pr-1">
        {quotes.map((q) => {
          const isSelected = q.symbol === selectedSymbol;
          const isUp = parseFloat(q.change) >= 0;

          return (
            <div
              key={q.security_id}
              onClick={() => onSelectSymbol(q.symbol)}
              className={`p-2.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between group ${
                isSelected
                  ? 'bg-indigo-950/40 border-indigo-600/70'
                  : 'bg-slate-900/40 border-slate-800/60 hover:bg-slate-850 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                    isUp ? 'bg-emerald-950/60 text-emerald-400' : 'bg-rose-950/60 text-rose-400'
                  }`}
                >
                  {isUp ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                </div>
                <div>
                  <div className="font-bold text-xs text-white group-hover:text-indigo-300 transition-colors">
                    {q.symbol}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    Vol: {(q.volume / 1000).toFixed(0)}k
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <div className="text-right">
                  <div className="text-xs font-mono font-bold text-slate-100">
                    ₹{parseFloat(q.ltp).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </div>
                  <div
                    className={`text-[10px] font-mono font-semibold ${
                      isUp ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {isUp ? '+' : ''}
                    {q.change_pct}%
                  </div>
                </div>

                <button
                  title="Trade this symbol"
                  onClick={(e) => {
                    e.stopPropagation();
                    onTradeSymbol(q.symbol, q.ltp);
                  }}
                  className="p-1 rounded bg-slate-800 hover:bg-indigo-600 text-slate-300 hover:text-white transition-all opacity-0 group-hover:opacity-100"
                >
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
