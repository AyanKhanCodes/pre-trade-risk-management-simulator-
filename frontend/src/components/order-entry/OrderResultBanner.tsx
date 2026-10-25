import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  ArrowRight,
  Hash,
  Clock,
  DollarSign,
  Zap,
} from 'lucide-react';
import { Order } from '../../types';
import { formatCurrency, formatDateTime } from '../../lib/utils';

interface OrderResultBannerProps {
  order: Order | null;
  onDismiss: () => void;
  onExecute?: (orderId: string) => Promise<void>;
}

export const OrderResultBanner: React.FC<OrderResultBannerProps> = ({
  order,
  onDismiss,
  onExecute,
}) => {
  const [showDetails, setShowDetails] = useState<boolean>(true);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);

  if (!order) return null;

  const isApproved = order.status === 'APPROVED';
  const isExecuted = order.status === 'EXECUTED';

  const handleExecute = async () => {
    if (!onExecute || isExecuting) return;
    setIsExecuting(true);
    try {
      await onExecute(order.order_id);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div
      className={`rounded-2xl border p-5 transition-all shadow-xl ${
        isApproved
          ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-100 glow-emerald'
          : 'bg-rose-950/25 border-rose-500/30 text-rose-100 glow-rose'
      }`}
    >
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div
            className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${
              isApproved
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
            }`}
          >
            {isApproved ? (
              <CheckCircle2 className="w-6 h-6 text-emerald-400" />
            ) : (
              <XCircle className="w-6 h-6 text-rose-400" />
            )}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span
                className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                  isApproved
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                }`}
              >
                {order.status}
              </span>
              <span className="text-sm font-semibold text-slate-100">
                Order #{order.order_id.slice(0, 8)}
              </span>
            </div>

            <div className="text-xs text-slate-300 mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
              <span>
                <strong>{order.side}</strong> {order.quantity} shares of{' '}
                <strong className="text-white font-mono">{order.symbol}</strong> @ {formatCurrency(order.price)}
              </span>
              <span className="text-slate-500">•</span>
              <span>Total Value: <strong>{formatCurrency(order.order_value)}</strong></span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-center">
          {isApproved && onExecute && (
            <button
              onClick={handleExecute}
              disabled={isExecuting}
              className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-emerald-950/60 transition-all cursor-pointer"
            >
              <Zap className="w-3.5 h-3.5" />
              {isExecuting ? 'Executing...' : 'Simulate Execution'}
            </button>
          )}
          {isExecuted && (
            <span className="px-3 py-1.5 rounded-lg bg-cyan-950/80 border border-cyan-800/80 text-cyan-300 font-bold text-xs flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Executed
            </span>
          )}
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-700/60 text-xs font-medium text-slate-200 hover:bg-slate-800 transition-colors flex items-center gap-1.5"
          >
            {showDetails ? (
              <>
                <span>Hide Audit Matrix</span>
                <ChevronUp className="w-3.5 h-3.5" />
              </>
            ) : (
              <>
                <span>Inspect 9 Risk Gates</span>
                <ChevronDown className="w-3.5 h-3.5" />
              </>
            )}
          </button>
          <button
            onClick={onDismiss}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-colors text-xs"
          >
            Dismiss
          </button>
        </div>
      </div>

      {/* Rejection Reasons Alert */}
      {!isApproved && order.rejection_reasons.length > 0 && (
        <div className="mt-4 p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/60 space-y-1.5">
          <div className="text-xs font-bold text-rose-300 flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            Decision Rationale (Risk Rejection):
          </div>
          <ul className="list-disc list-inside space-y-1 text-xs text-rose-200 pl-1">
            {order.rejection_reasons.map((reason, idx) => (
              <li key={idx} className="font-medium">
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Detailed Risk Checks Matrix */}
      {showDetails && order.risk_checks && order.risk_checks.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-800/80">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
            <span>Deterministic Risk Engine Audit Trail</span>
            <span className="font-mono text-[10px] text-slate-500">
              Evaluated {order.risk_checks.length} Rules in Parallel
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
            {order.risk_checks.map((check) => {
              const passed = check.passed;
              return (
                <div
                  key={check.rule_id}
                  className={`p-2.5 rounded-xl border text-xs flex flex-col justify-between ${
                    passed
                      ? 'bg-slate-900/60 border-slate-800/80 text-slate-300'
                      : 'bg-rose-950/30 border-rose-800/60 text-rose-200'
                  }`}
                >
                  <div className="flex items-start justify-between gap-1 mb-1">
                    <div className="flex items-center gap-1.5 font-semibold text-slate-200">
                      <span className="font-mono text-[10px] px-1 py-0.2 rounded bg-slate-800 text-slate-400">
                        {check.rule_id}
                      </span>
                      <span className="truncate">{check.rule_name}</span>
                    </div>
                    {passed ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                    )}
                  </div>
                  <div className="text-[11px] text-slate-400">
                    {passed ? (
                      <span className="text-emerald-400/90 font-medium">PASS</span>
                    ) : (
                      <span className="text-rose-400 font-medium">{check.reason}</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
