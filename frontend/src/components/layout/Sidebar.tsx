import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  Send,
  History,
  Sliders,
  BarChart3,
  Wifi,
  WifiOff,
  AlertTriangle,
  Ban,
  CheckCircle2,
  LineChart,
  Filter,
  Wallet,
} from 'lucide-react';
import { api } from '../../lib/api';
import { RiskConfig } from '../../types';
import { formatCurrency } from '../../lib/utils';

export type NavTab =
  | 'workstation'
  | 'screener'
  | 'portfolio'
  | 'trade'
  | 'orders'
  | 'rules'
  | 'analytics';

interface SidebarProps {
  currentTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  config: RiskConfig | null;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onTabChange, config }) => {
  const [isOnline, setIsOnline] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    const check = async () => {
      try {
        await api.checkHealth();
        if (isMounted) setIsOnline(true);
      } catch {
        if (isMounted) setIsOnline(false);
      }
    };
    check();
    const interval = setInterval(check, 10000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const navItems = [
    {
      id: 'workstation' as NavTab,
      label: 'Market Workstation',
      desc: 'NSE charts & live watchlist',
      icon: LineChart,
    },
    {
      id: 'screener' as NavTab,
      label: 'Stock Screener',
      desc: 'Discover & preliminary risk',
      icon: Filter,
    },
    {
      id: 'portfolio' as NavTab,
      label: 'Simulated Portfolio',
      desc: 'Cash & mark-to-market P&L',
      icon: Wallet,
    },
    {
      id: 'trade' as NavTab,
      label: 'Order Execution',
      desc: 'Submit & pre-validate orders',
      icon: Send,
    },
    {
      id: 'orders' as NavTab,
      label: 'Order Audit History',
      desc: 'Inspect approval & rejections',
      icon: History,
    },
    {
      id: 'rules' as NavTab,
      label: 'Risk Rules Engine',
      desc: 'Configurable limits & compliance',
      icon: Sliders,
    },
    {
      id: 'analytics' as NavTab,
      label: 'Risk Analytics',
      desc: 'Notional exposure & telemetry',
      icon: BarChart3,
    },
  ];

  return (
    <aside className="w-full lg:w-72 bg-[#0a0e18] border-r border-slate-800 flex flex-col justify-between shrink-0">
      <div>
        {/* Brand header */}
        <div className="p-5 border-b border-slate-800 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center shadow-lg shadow-emerald-950/60 ring-1 ring-emerald-400/30">
            <ShieldAlert className="w-5 h-5 text-slate-950 font-bold" />
          </div>
          <div>
            <div className="text-sm font-extrabold tracking-wider text-slate-100 flex items-center gap-1.5">
              <span>AEGIS</span>
              <span className="text-emerald-400 font-mono text-xs font-semibold px-1.5 py-0.2 rounded bg-emerald-950/60 border border-emerald-800/40">RISK</span>
            </div>
            <div className="text-[11px] text-slate-400 font-medium">Pre-Trade Validation Engine</div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1">
          <div className="px-3 py-2 text-[10px] font-semibold tracking-wider text-slate-500 uppercase">
            Platform Modules
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center gap-3.5 px-3.5 py-3 rounded-xl text-left transition-all duration-200 group relative ${
                  isActive
                    ? 'bg-slate-800/90 text-white shadow-md border border-slate-700/60'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
                }`}
              >
                {isActive && (
                  <div className="absolute left-0 top-2 bottom-2 w-1 bg-emerald-400 rounded-r-full shadow-[0_0_10px_#10b981]" />
                )}
                <div
                  className={`p-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/30'
                      : 'bg-slate-900 text-slate-400 group-hover:text-slate-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className={`text-xs font-semibold tracking-tight ${isActive ? 'text-slate-100' : 'text-slate-300'}`}>
                    {item.label}
                  </div>
                  <div className="text-[10px] text-slate-500 truncate">{item.desc}</div>
                </div>
              </button>
            );
          })}
        </nav>

        {/* Quick parameters snapshot */}
        {config && (
          <div className="mx-3 mt-4 p-3.5 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-2.5">
            <div className="flex items-center justify-between text-[11px] font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5">
              <span className="flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-emerald-400" />
                Active Thresholds
              </span>
              <span className="text-[10px] text-emerald-400 bg-emerald-950/40 px-1.5 py-0.5 rounded border border-emerald-900/40">
                Live
              </span>
            </div>

            <div className="space-y-1.5 text-[11px]">
              <div className="flex justify-between items-center text-slate-400">
                <span>Max Order Value:</span>
                <span className="font-mono text-slate-200 font-semibold">{formatCurrency(config.max_order_value)}</span>
              </div>
              <div className="flex justify-between items-center text-slate-400">
                <span className="flex items-center gap-1">
                  <span>Min Price:</span>
                  <span className="text-[9px] text-purple-400 bg-purple-950/50 px-1 rounded">Penny</span>
                </span>
                <span className="font-mono text-purple-300 font-semibold">{formatCurrency(config.min_price)}</span>
              </div>
              <div className="flex justify-between items-center text-slate-400">
                <span>Max Quantity:</span>
                <span className="font-mono text-slate-200 font-semibold">{config.max_quantity.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center text-slate-400 pt-1 border-t border-slate-800/60">
                <span className="flex items-center gap-1 text-amber-400">
                  <Ban className="w-3 h-3" />
                  Restricted:
                </span>
                <span className="font-mono text-amber-300 font-semibold truncate max-w-[100px]" title={config.restricted_symbols.join(', ')}>
                  {config.restricted_symbols.join(', ') || 'None'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Sidebar Footer with Health Status */}
      <div className="p-4 border-t border-slate-800/80 bg-[#080c14]/70">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2">
            {isOnline ? (
              <>
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 ring-4 ring-emerald-500/20 animate-pulse" />
                <span className="text-slate-300 font-medium text-xs">Engine Online</span>
              </>
            ) : (
              <>
                <div className="w-2.5 h-2.5 rounded-full bg-rose-500 ring-4 ring-rose-500/20" />
                <span className="text-rose-400 font-medium text-xs">Engine Offline</span>
              </>
            )}
          </div>
          <div className="flex items-center gap-1 text-[11px] font-mono text-slate-500">
            {isOnline ? <Wifi className="w-3 h-3 text-emerald-400" /> : <WifiOff className="w-3 h-3 text-rose-400" />}
            FastAPI:8000
          </div>
        </div>
      </div>
    </aside>
  );
};
