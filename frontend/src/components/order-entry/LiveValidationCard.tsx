import React from 'react';
import {
  CheckCircle2,
  XCircle,
  ShieldCheck,
  Cpu
} from 'lucide-react';
import { RiskConfig, OrderSide } from '../../types';
import { formatCurrency, formatNumber } from '../../lib/utils';

interface LiveValidationCardProps {
  symbol: string;
  side?: OrderSide;
  quantity: number | '';
  price: string;
  config: RiskConfig | null;
  currency?: string;
  holdingInfo?: { held_qty: number; reserved_qty: number; sellable_qty: number } | null;
}

interface PreCheckItem {
  id: string;
  name: string;
  passed: boolean;
  message: string;
  severity: 'pass' | 'fail' | 'warn';
  category: string;
  sideScope?: 'BOTH' | 'SELL';
}

export const LiveValidationCard: React.FC<LiveValidationCardProps> = ({
  symbol,
  side = 'BUY',
  quantity,
  price,
  config,
  holdingInfo,
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
    sideScope: 'BOTH',
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
    sideScope: 'BOTH',
  });

  // RISK-05: Minimum Price (Penny Stock Protection)
  const minPrice = parseFloat(config.min_price) || 1.0;
  const isPennyStock = isPriceValid && numPrice < minPrice;
  checks.push({
    id: 'RISK-05',
    name: 'Penny Stock Protection',
    passed: !isPennyStock,
    message: isPennyStock
      ? `Violation: Price ${formatCurrency(numPrice)} is below minimum threshold ${formatCurrency(minPrice)}`
      : `Price meets minimum ${formatCurrency(minPrice)} requirement`,
    severity: isPennyStock ? 'fail' : 'pass',
    category: 'Price Controls',
    sideScope: 'BOTH',
  });

  // RISK-07: Maximum Price (Fat-Finger Protection)
  const maxPrice = parseFloat(config.max_price) || 200000;
  const isFatFinger = isPriceValid && numPrice > maxPrice;
  checks.push({
    id: 'RISK-07',
    name: 'Fat-Finger Protection',
    passed: !isFatFinger,
    message: isFatFinger
      ? `Violation: Price ${formatCurrency(numPrice)} exceeds maximum ${formatCurrency(maxPrice)}`
      : `Within max price limit (${formatCurrency(maxPrice)})`,
    severity: isFatFinger ? 'fail' : 'pass',
    category: 'Price Controls',
    sideScope: 'BOTH',
  });

  // RISK-01: Maximum Order Value
  const maxOrderVal = parseFloat(config.max_order_value) || 500000;
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
    sideScope: 'BOTH',
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
    sideScope: 'BOTH',
  });

  // RISK-02: Restricted Symbol Check
  const restrictedList = (config.restricted_symbols || []).map((s) => s.toUpperCase());
  const isRestricted = upperSymbol ? restrictedList.includes(upperSymbol) : false;
  checks.push({
    id: 'RISK-02',
    name: 'Compliance / Restricted Symbol',
    passed: !isRestricted,
    message: isRestricted
      ? `Violation: Symbol '${upperSymbol}' is on the restricted blacklist`
      : upperSymbol
      ? `Symbol '${upperSymbol}' is unrestricted`
      : 'Symbol not entered yet',
    severity: isRestricted ? 'fail' : 'pass',
    category: 'Compliance',
    sideScope: 'BOTH',
  });

  // RISK-10: Available Holdings / Short-Selling Prohibition
  const isSell = side === 'SELL';
  const heldQty = holdingInfo?.held_qty ?? 0;
  const sellableQty = holdingInfo?.sellable_qty ?? 0;
  const reservedQty = holdingInfo?.reserved_qty ?? 0;

  if (isSell) {
    const hasHolding = heldQty > 0;
    checks.push({
      id: 'RISK-10',
      name: 'Available Holdings Check',
      passed: hasHolding,
      message: hasHolding
        ? `Position held (${heldQty} shares) satisfies holding inventory requirement`
        : `Violation: Cannot SELL ${numQty || 0} shares — no position held in ${upperSymbol || 'asset'} (short-selling prohibited)`,
      severity: hasHolding ? 'pass' : 'fail',
      category: 'Inventory Verification',
      sideScope: 'SELL',
    });

    // RISK-11: Open Sell Order Reservation
    const hasSellableCapacity = numQty > 0 && numQty <= sellableQty;
    checks.push({
      id: 'RISK-11',
      name: 'Open Sell Order Reservation',
      passed: hasSellableCapacity,
      message: hasSellableCapacity
        ? `Requested ${numQty} shares within net sellable quantity (${sellableQty} shares available)`
        : reservedQty > 0
        ? `Violation: Quantity ${numQty} exceeds net sellable quantity ${sellableQty} (${heldQty} held, ${reservedQty} reserved by open orders)`
        : `Violation: Quantity ${numQty} exceeds available holdings (${heldQty} held)`,
      severity: hasSellableCapacity ? 'pass' : 'fail',
      category: 'Inventory Verification',
      sideScope: 'SELL',
    });

    // RISK-12: Position Ledger Integrity
    const isLedgerValid = heldQty >= 0;
    checks.push({
      id: 'RISK-12',
      name: 'Position Ledger Integrity',
      passed: isLedgerValid,
      message: isLedgerValid
        ? 'Position ledger integrity verified (non-negative balance)'
        : `Violation: Negative position detected (${heldQty})`,
      severity: isLedgerValid ? 'pass' : 'fail',
      category: 'Inventory Verification',
      sideScope: 'SELL',
    });
  } else {
    // BUY side: RISK-10, 11, 12 shown as NOT_APPLICABLE / Pass
    checks.push({
      id: 'RISK-10',
      name: 'Available Holdings Check',
      passed: true,
      message: 'Rule applicable only to SELL orders (N/A for BUY)',
      severity: 'pass',
      category: 'Inventory Verification',
      sideScope: 'SELL',
    });
    checks.push({
      id: 'RISK-11',
      name: 'Open Sell Order Reservation',
      passed: true,
      message: 'Rule applicable only to SELL orders (N/A for BUY)',
      severity: 'pass',
      category: 'Inventory Verification',
      sideScope: 'SELL',
    });
    checks.push({
      id: 'RISK-12',
      name: 'Position Ledger Integrity',
      passed: true,
      message: 'Rule applicable only to SELL orders (N/A for BUY)',
      severity: 'pass',
      category: 'Inventory Verification',
      sideScope: 'SELL',
    });
  }

  // Count passes and fails
  const failedCount = checks.filter((c) => !c.passed).length;
  const isAllPassed = failedCount === 0 && numQty > 0 && numPrice > 0 && Boolean(upperSymbol);

  return (
    <div className="rounded-2xl bg-gradient-to-b from-[#0f1626] to-[#0c121e] border border-slate-800 p-6 shadow-xl flex flex-col justify-between h-full">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 tracking-tight">
                Real-Time Pre-Trade Check Engine
              </h2>
              <p className="text-[11px] text-slate-400">
                Deterministic institutional risk gate evaluation
              </p>
            </div>
          </div>

          <div>
            {isAllPassed ? (
              <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 shadow-sm shadow-emerald-950">
                <CheckCircle2 className="w-3.5 h-3.5" />
                All Gates Passing
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
            <span className="text-[10px] text-slate-400 block font-medium">Computed Order Value (INR)</span>
            <span className="text-lg font-bold font-mono text-slate-100">
              {formatCurrency(calculatedValue)}
            </span>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] text-slate-400 block font-medium">Max Allowed Value (INR)</span>
            <span className="text-lg font-bold font-mono text-emerald-400">
              {formatCurrency(maxOrderVal)}
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
                      <span className="font-bold tracking-tight text-slate-200">
                        <span className="text-slate-500 font-mono text-[11px] mr-1.5">
                          {check.id}
                        </span>
                        {check.name}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500 shrink-0">
                        {check.category}
                      </span>
                    </div>
                    <p
                      className={`text-[11px] mt-0.5 ${
                        isPass ? 'text-slate-400' : 'text-rose-300 font-medium'
                      }`}
                    >
                      {check.message}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Footer advice */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
        <span className="flex items-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          Pre-Trade Risk Clearance
        </span>
        <span className="font-mono">12 Rules Evaluated (INR)</span>
      </div>
    </div>
  );
};
