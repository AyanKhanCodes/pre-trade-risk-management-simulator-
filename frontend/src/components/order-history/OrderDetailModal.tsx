import React from 'react';
import {
  X,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  ShieldAlert,
  Clock,
  Tag,
  DollarSign,
  Layers,
  ArrowRight
} from 'lucide-react';
import { Order } from '../../types';
import { formatCurrency, formatDateTime, formatNumber } from '../../lib/utils';

interface OrderDetailModalProps {
  order: Order | null;
  onClose: () => void;
}

export const OrderDetailModal: React.FC<OrderDetailModalProps> = ({ order, onClose }) => {
  if (!order) return null;

  const isApproved = order.status === 'APPROVED';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#0f1626] border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                isApproved
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
              }`}
            >
              {isApproved ? (
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
              ) : (
                <ShieldAlert className="w-5 h-5 text-rose-400" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-100">
                  Order Risk Audit Dossier
                </h3>
                <span
                  className={`text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                    isApproved
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                  }`}
                >
                  {order.status}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                UUID: {order.order_id}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800/80 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-5 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Order Snapshot Specs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Symbol</span>
              <span className="text-base font-bold font-mono text-slate-100">{order.symbol}</span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Side</span>
              <span
                className={`text-base font-bold uppercase tracking-wider ${
                  order.side === 'BUY' ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {order.side}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Quantity</span>
              <span className="text-base font-bold font-mono text-slate-100">
                {formatNumber(order.quantity)}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Price / Unit</span>
              <span className="text-base font-bold font-mono text-slate-100">
                {formatCurrency(order.price)}
              </span>
            </div>
          </div>

          {/* Notional & Timestamp */}
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col sm:flex-row justify-between sm:items-center gap-2">
            <div>
              <span className="text-xs text-slate-400">Total Notional Value:</span>
              <div className="text-xl font-bold font-mono text-emerald-400">
                {formatCurrency(order.order_value)}
              </div>
            </div>
            <div className="text-xs text-slate-400 flex items-center gap-1.5 font-mono">
              <Clock className="w-4 h-4 text-slate-500" />
              <span>Created: {formatDateTime(order.created_at)}</span>
            </div>
          </div>

          {/* Rejection Reasons */}
          {!isApproved && order.rejection_reasons.length > 0 && (
            <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-800/60">
              <h4 className="text-xs font-bold text-rose-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <XCircle className="w-4 h-4 text-rose-400" />
                Violated Risk Policies ({order.rejection_reasons.length})
              </h4>
              <ul className="list-disc list-inside space-y-1.5 text-xs text-rose-200">
                {order.rejection_reasons.map((r, i) => (
                  <li key={i} className="font-medium">
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Detailed Gates Evaluated */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
              Risk Engine Evaluation Matrix
            </h4>
            <div className="space-y-2">
              {order.risk_checks && order.risk_checks.length > 0 ? (
                order.risk_checks.map((check) => {
                  const pass = check.passed;
                  return (
                    <div
                      key={check.rule_id}
                      className={`p-3 rounded-xl border text-xs flex items-start justify-between gap-3 ${
                        pass
                          ? 'bg-slate-900/40 border-slate-800/60 text-slate-300'
                          : 'bg-rose-950/30 border-rose-800/60 text-rose-200'
                      }`}
                    >
                      <div className="flex items-start gap-2.5">
                        <div className="mt-0.5 shrink-0">
                          {pass ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          ) : (
                            <XCircle className="w-4 h-4 text-rose-400" />
                          )}
                        </div>
                        <div>
                          <div className="font-semibold text-slate-100 flex items-center gap-1.5">
                            <span className="font-mono text-[10px] px-1 py-0.2 rounded bg-slate-800 text-slate-400">
                              {check.rule_id}
                            </span>
                            <span>{check.rule_name}</span>
                          </div>
                          {!pass && (
                            <p className="text-[11px] text-rose-400 mt-1 font-medium">
                              {check.reason}
                            </p>
                          )}
                        </div>
                      </div>

                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                          pass
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}
                      >
                        {pass ? 'PASSED' : 'REJECTED'}
                      </span>
                    </div>
                  );
                })
              ) : (
                <div className="text-xs text-slate-500 italic p-3 text-center">
                  No individual risk check records available for this order.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 bg-[#080c14] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
          >
            Close Dossier
          </button>
        </div>
      </div>
    </div>
  );
};
