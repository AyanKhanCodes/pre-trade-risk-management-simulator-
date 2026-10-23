import React from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  ShieldCheck,
  TrendingUp,
  Cpu
} from 'lucide-react';
import { RiskConfig } from '../../types';
import { formatCurrency, formatNumber } from '../../lib/utils';

interface LiveValidationCardProps {
  symbol: string;
  quantity: number | '';
  price: string;
  config: RiskConfig | null;
}

interface PreCheckItem {
  id: string;
  name: string;
  passed: boolean;
  message: string;
  severity: 'pass' | 'fail' | 'warn';
  category: string;
}

export const LiveValidationCard: React.FC<LiveValidationCardProps> = ({
  symbol,
  quantity,
  price,
  config,
}) => {
  const numQty = typeof quantity === 'number' ? quantity : 0;
  const numPrice = parseFloat(price) || 0;
  const calculatedValue = numQty * numPrice;
  const upperSymbol = symbol.trim().toUpperCase();

  // Evaluate pre-checks based on current inputs
  const checks: PreCheckItem[] = [];

  if (!config) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-center text-slate-500 text-sm">
        Loading risk configuration parameters...
      </div>
    );
  }

  // RISK-03: Quantity Validity
  const isQtyValid = numQty > 0 && Number.isInteger(numQty);
  checks.push({
    id: 'RISK-03',
    name: 'Quantity Validity',
    passed: isQtyValid,
    message: isQtyValid
      ? `Positive integer (${formatNumber(numQty)} units)`
      : 'Must be positive integer > 0',
    severity: isQtyValid ? 'pass' : 'fail',
    category: 'Input Validation',
  });

  // RISK-04: Price Validity
  const isPriceValid = numPrice > 0;
  checks.push({
    id: 'RISK-04',
    name: 'Price Validity',
    passed: isPriceValid,
    message: isPriceValid
      ? `Positive decimal (${formatCurrency(numPrice)})`
      : 'Price must be positive > 0',
    severity: isPriceValid ? 'pass' : 'fail',
    category: 'Input Validation',
  });

  // RISK-05: Minimum Price (Penny Stock Protection)
  const minPrice = parseFloat(config.min_price) || 1.0;
  const isPennyStock = isPriceValid && numPrice < minPrice;
  checks.push({
    id: 'RISK-05',
    name: 'Penny Stock Protection',
    passed: !isPennyStock,
    message: isPennyStock
      ? `Violation: Price $${numPrice.toFixed(2)} is below minimum threshold ${formatCurrency(minPrice)}`
      : `Price meets minimum ${formatCurrency(minPrice)} requirement`,
    severity: isPennyStock ? 'fail' : 'pass',
    category: 'Price Controls',
  });

  // RISK-07: Maximum Price (Fat-Finger Protection)
  const maxPrice = parseFloat(config.max_price) || 50000;
  const isFatFinger = isPriceValid && numPrice > maxPrice;
  checks.push({
    id: 'RISK-07',
    name: 'Fat-Finger Protection',
    passed: !isFatFinger,
    message: isFatFinger
      ? `Violation: Price $${numPrice.toFixed(2)} exceeds maximum ${formatCurrency(maxPrice)}`
      : `Within max price limit (${formatCurrency(maxPrice)})`,
    severity: isFatFinger ? 'fail' : 'pass',
    category: 'Price Controls',
  });

  // RISK-01: Maximum Order Value
  const maxOrderVal = parseFloat(config.max_order_value) || 10000;
  const isValueExceeded = calculatedValue > maxOrderVal;
  checks.push({
    id: 'RISK-01',
    name: 'Max Order Notional',
    passed: !isValueExceeded,
    message: isValueExceeded
      ? `Violation: Order value ${formatCurrency(calculatedValue)} exceeds limit of ${formatCurrency(maxOrderVal)}`
      : `Order value ${formatCurrency(calculatedValue)} ≤ limit of ${formatCurrency(maxOrderVal)}`,
    severity: isValueExceeded ? 'fail' : 'pass',
    category: 'Position Limits',
  });

  // RISK-06: Maximum Quantity
  const maxQty = config.max_quantity || 10000;
  const isQtyExceeded = numQty > maxQty;
  checks.push({
    id: 'RISK-06',
    name: 'Position Quantity Cap',
    passed: !isQtyExceeded,
    message: isQtyExceeded
      ? `Violation: Quantity ${formatNumber(numQty)} exceeds cap of ${formatNumber(maxQty)}`
      : `Quantity within cap (${formatNumber(maxQty)} shares)`,
    severity: isQtyExceeded ? 'fail' : 'pass',
    category: 'Position Limits',
  });

  // RISK-02: Restricted Symbol Check
  const restrictedList = config.restricted_symbols.map((s) => s.toUpperCase());
  const isRestricted = upperSymbol ? restrictedList.includes(upperSymbol) : false;
  checks.push({
    id: 'RISK-02',
    name: 'Compliance / Restricted Symbol',
    passed: !isRestricted,
    message: isRestricted
      ? `Violation: Symbol '${upperSymbol}' is prohibited from trading`
      : upperSymbol
      ? `Symbol '${upperSymbol}' is cleared for trading`
      : 'Awaiting symbol input',
    severity: isRestricted ? 'fail' : 'pass',
    category: 'Compliance',
  });

  // RISK-08 & 09: Activity Limits (Server-evaluated)
  checks.push({
    id: 'RISK-08 & 09',
    name: 'Daily Activity & Notional Caps',
    passed: true,
    message: `Evaluated against daily aggregate limits (Max ${config.max_daily_orders} orders / ${formatCurrency(config.max_daily_notional)})`,
    severity: 'pass',
    category: 'Activity Limits',
  });

  const allPassed = checks.every((c) => c.passed);
  const failedCount = checks.filter((c) => !c.passed).length;

  return (
    <div className="rounded-2xl bg-gradient-to-b from-[#0f1626] to-[#0c121e] border border-slate-800 p-5 shadow-xl flex flex-col justify-between h-full">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-4">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-slate-100 tracking-tight">
              Real-Time Pre-Trade Check Engine
            </h3>
          </div>
          <div className="flex items-center gap-1.5">
            {allPassed ? (
              <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 shadow-sm shadow-emerald-950">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Pre-Check Clear
              </span>
            ) : (
              <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1 shadow-sm shadow-rose-950">
                <XCircle className="w-3.5 h-3.5" />
                {failedCount} Rule {failedCount === 1 ? 'Violation' : 'Violations'}
              </span>
            )}
          </div>
        </div>

        {/* Current Order Sizing Summary */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] text-slate-400 block font-medium">Computed Order Value</span>
            <span className="text-lg font-bold font-mono text-slate-100">
              {formatCurrency(calculatedValue)}
            </span>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] text-slate-400 block font-medium">Max Allowed Value</span>
            <span className="text-lg font-bold font-mono text-emerald-400">
              {formatCurrency(config.max_order_value)}
            </span>
          </div>
        </div>

        {/* Live Rules Matrix */}
        <div className="space-y-2">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-1">
            Active Gate Status
          </div>
          <div className="space-y-1.5 max-h-[360px] overflow-y-auto pr-1">
            {checks.map((check) => {
              const isPass = check.passed;
              return (
                <div
                  key={check.id}
                  className={`p-2.5 rounded-xl border transition-all text-xs flex items-start gap-3 ${
                    isPass
                      ? 'bg-slate-900/40 border-slate-800/60 text-slate-300'
                      : 'bg-rose-950/20 border-rose-800/50 text-rose-200'
                  }`}
                >
                  <div className="mt-0.5 shrink-0">
                    {isPass ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                        <span className="font-mono text-[10px] px-1 py-0.2 rounded bg-slate-800 text-slate-400">
                          {check.id}
                        </span>
                        <span>{check.name}</span>
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {check.category}
                      </span>
                    </div>
                    <div
                      className={`text-[11px] mt-0.5 leading-relaxed ${
                        isPass ? 'text-slate-400' : 'text-rose-400 font-medium'
                      }`}
                    >
                      {check.message}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 flex items-center justify-between">
        <span className="flex items-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          Full non-short-circuiting evaluation
        </span>
        <span>Deterministic</span>
      </div>
    </div>
  );
};
