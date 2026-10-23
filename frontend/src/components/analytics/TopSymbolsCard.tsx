import React from 'react';
import { Tag, TrendingUp } from 'lucide-react';
import { TopSymbolStat } from '../../types';

interface TopSymbolsCardProps {
  symbols: TopSymbolStat[];
}

export const TopSymbolsCard: React.FC<TopSymbolsCardProps> = ({ symbols }) => {
  return (
    <div className="rounded-2xl bg-[#0f1626] border border-slate-800 p-5 shadow-xl">
      <div className="flex items-center gap-2 mb-1">
        <Tag className="w-4 h-4 text-emerald-400" />
        <h3 className="text-sm font-bold text-slate-100">
          Most Active Evaluated Tickers
        </h3>
      </div>
      <p className="text-xs text-slate-400 mb-4">
        Highest frequency securities submitted to the simulator
      </p>

      {symbols.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500 italic">
          No trading activity recorded yet.
        </div>
      ) : (
        <div className="space-y-2">
          {symbols.map((item, idx) => (
            <div
              key={item.symbol}
              className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs"
            >
              <div className="flex items-center gap-2.5">
                <span className="w-5 h-5 rounded-lg bg-slate-800 text-slate-400 font-mono text-[10px] flex items-center justify-center font-bold">
                  {idx + 1}
                </span>
                <span className="font-mono font-bold text-slate-100 text-sm">
                  {item.symbol}
                </span>
              </div>
              <span className="font-mono text-emerald-400 font-semibold px-2 py-0.5 rounded bg-emerald-950/40 border border-emerald-900/50">
                {item.count} {item.count === 1 ? 'Order' : 'Orders'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
