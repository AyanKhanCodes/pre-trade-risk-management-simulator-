import React from 'react';
import {
  TrendingUp,
  CheckCircle2,
  XCircle,
  DollarSign,
  Activity,
  Layers,
  BarChart3
} from 'lucide-react';
import { OrderStatsSummary, RiskConfig } from '../../types';
import { formatCurrency, formatNumber } from '../../lib/utils';

interface StatsKPIsProps {
  stats: OrderStatsSummary | null;
  config: RiskConfig | null;
}

export const StatsKPIs: React.FC<StatsKPIsProps> = ({ stats, config }) => {
  if (!stats) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 rounded-2xl bg-slate-900/40 border border-slate-800 animate-pulse" />
        ))}
      </div>
    );
  }

  const today = stats.today;
  const allTime = stats.all_time;

  const approvalRate = today.approval_rate;
  const approvalRateColor =
    approvalRate >= 75
      ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
      : approvalRate >= 50
      ? 'text-amber-400 bg-amber-500/10 border-amber-500/30'
      : 'text-rose-400 bg-rose-500/10 border-rose-500/30';

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* KPI 1: Orders Today */}
      <div className="p-5 rounded-2xl bg-[#0f1626] border border-slate-800 shadow-xl flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2 font-medium">
            <span>Orders Today</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold font-mono text-slate-100">
            {formatNumber(today.total_orders)}
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
          <span className="text-emerald-400 flex items-center gap-1 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            {today.approved} Approved
          </span>
          <span className="text-rose-400 flex items-center gap-1 font-medium">
            <XCircle className="w-3.5 h-3.5" />
            {today.rejected} Rejected
          </span>
        </div>
      </div>

      {/* KPI 2: Approval Rate */}
      <div className="p-5 rounded-2xl bg-[#0f1626] border border-slate-800 shadow-xl flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2 font-medium">
            <span>Approval Rate (Today)</span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${approvalRateColor}`}>
              {today.total_orders > 0 ? `${approvalRate}%` : 'N/A'}
            </span>
          </div>
          <div className="text-3xl font-extrabold font-mono text-slate-100">
            {today.total_orders > 0 ? `${approvalRate}%` : '0.0%'}
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-slate-800/80 text-xs text-slate-400">
          <span>All-time average: </span>
          <strong className="text-slate-200 font-mono">{allTime.approval_rate}%</strong>
        </div>
      </div>

      {/* KPI 3: Today's Notional Value */}
      <div className="p-5 rounded-2xl bg-[#0f1626] border border-slate-800 shadow-xl flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2 font-medium">
            <span>Notional Exposure (Today)</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold font-mono text-emerald-400 truncate">
            {formatCurrency(today.total_notional)}
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-slate-800/80 text-xs text-slate-400 flex justify-between">
          <span>Daily Limit:</span>
          <span className="font-mono text-slate-200">
            {config ? formatCurrency(config.max_daily_notional) : '₹50,00,000'}
          </span>
        </div>
      </div>

      {/* KPI 4: All-Time Cumulative */}
      <div className="p-5 rounded-2xl bg-[#0f1626] border border-slate-800 shadow-xl flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2 font-medium">
            <span>Total Cumulative Orders</span>
            <Layers className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-extrabold font-mono text-slate-100">
            {formatNumber(allTime.total_orders)}
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-slate-800/80 text-xs text-slate-400 flex justify-between">
          <span>Total Notional:</span>
          <span className="font-mono font-bold text-slate-200">
            {formatCurrency(allTime.total_notional)}
          </span>
        </div>
      </div>
    </div>
  );
};
