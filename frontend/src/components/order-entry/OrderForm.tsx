import React, { useState } from 'react';
import {
  Send,
  Zap,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Layers,
  AlertCircle,
  Sparkles
} from 'lucide-react';
import { OrderSide, OrderCreateRequest, RiskConfig } from '../../types';
import { formatCurrency } from '../../lib/utils';

interface OrderFormProps {
  onSubmit: (order: OrderCreateRequest) => Promise<void>;
  isLoading: boolean;
  config: RiskConfig | null;
  onValuesChange: (values: { symbol: string; side: OrderSide; quantity: number | ''; price: string }) => void;
  initialSymbol?: string;
  initialPrice?: string;
}

export const OrderForm: React.FC<OrderFormProps> = ({
  onSubmit,
  isLoading,
  config,
  onValuesChange,
  initialSymbol,
  initialPrice,
}) => {
  const [symbol, setSymbol] = useState<string>(initialSymbol || 'RELIANCE');
  const [side, setSide] = useState<OrderSide>('BUY');
  const [quantity, setQuantity] = useState<number | ''>(10);
  const [price, setPrice] = useState<string>(initialPrice || '2945.50');
  const [currency, setCurrency] = useState<string>('INR');
  const [formError, setFormError] = useState<string | null>(null);

  // Sync when initial props change
  React.useEffect(() => {
    if (initialSymbol) {
      setSymbol(initialSymbol);
      if (initialPrice) setPrice(initialPrice);
      notifyChange(initialSymbol, side, quantity, initialPrice || price);
    }
  }, [initialSymbol, initialPrice]);

  const notifyChange = (newSymbol: string, newSide: OrderSide, newQty: number | '', newPrice: string) => {
    onValuesChange({
      symbol: newSymbol,
      side: newSide,
      quantity: newQty,
      price: newPrice,
    });
  };

  const handleSymbolChange = (val: string) => {
    const clean = val.toUpperCase().replace(/[^A-Z0-9&-]/g, '');
    setSymbol(clean);
    setFormError(null);
    notifyChange(clean, side, quantity, price);
  };

  const handleSideChange = (newSide: OrderSide) => {
    setSide(newSide);
    notifyChange(symbol, newSide, quantity, price);
  };

  const handleQuantityChange = (val: string) => {
    if (val === '') {
      setQuantity('');
      notifyChange(symbol, side, '', price);
      return;
    }
    const parsed = parseInt(val, 10);
    if (!isNaN(parsed)) {
      setQuantity(parsed);
      setFormError(null);
      notifyChange(symbol, side, parsed, price);
    }
  };

  const handlePriceChange = (val: string) => {
    setPrice(val);
    setFormError(null);
    notifyChange(symbol, side, quantity, val);
  };

  const applyPreset = (
    presetSymbol: string,
    presetSide: OrderSide,
    presetQty: number,
    presetPrice: string,
    presetCurrency: string = 'INR'
  ) => {
    setSymbol(presetSymbol);
    setSide(presetSide);
    setQuantity(presetQty);
    setPrice(presetPrice);
    setCurrency(presetCurrency);
    setFormError(null);
    notifyChange(presetSymbol, presetSide, presetQty, presetPrice);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!symbol.trim()) {
      setFormError('Ticker symbol is required.');
      return;
    }

    if (quantity === '' || quantity <= 0) {
      setFormError('Quantity must be a positive integer.');
      return;
    }

    const parsedPrice = parseFloat(price);
    if (isNaN(parsedPrice) || parsedPrice <= 0) {
      setFormError('Price must be a positive number.');
      return;
    }

    try {
      await onSubmit({
        symbol: symbol.trim(),
        side,
        quantity,
        price,
        currency,
      });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message);
      } else {
        setFormError('Failed to submit order.');
      }
    }
  };

  const numQty = typeof quantity === 'number' ? quantity : 0;
  const numPrice = parseFloat(price) || 0;
  const orderValue = numQty * numPrice;

  return (
    <div className="rounded-2xl bg-gradient-to-b from-[#0f1626] to-[#0c121e] border border-slate-800 p-6 shadow-xl flex flex-col justify-between h-full">
      <div>
        {/* Title */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Send className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 tracking-tight">
                Order Entry Terminal
              </h2>
              <p className="text-[11px] text-slate-400">
                Submit orders to the automated risk clearinghouse
              </p>
            </div>
          </div>
        </div>

        {/* Professor Quick-Test Scenarios */}
        <div className="mb-5 p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-400 mb-2">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Demonstration Test Scenarios:</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
            <button
              type="button"
              onClick={() => applyPreset('AAPL', 'BUY', 10, '150.00')}
              className="px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-left border border-slate-700/50 transition-colors"
            >
              <div className="text-[11px] font-bold text-emerald-400">✓ Valid Order</div>
              <div className="text-[10px] text-slate-400 font-mono">AAPL 10 @ $150</div>
            </button>

            <button
              type="button"
              onClick={() => applyPreset('PENN', 'BUY', 100, '0.01')}
              className="px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-left border border-slate-700/50 transition-colors"
            >
              <div className="text-[11px] font-bold text-purple-400">✗ Penny Stock ($0.01)</div>
              <div className="text-[10px] text-slate-400 font-mono">PENN 100 @ $0.01</div>
            </button>

            <button
              type="button"
              onClick={() => applyPreset('TSLA', 'BUY', 5, '100.00')}
              className="px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-left border border-slate-700/50 transition-colors"
            >
              <div className="text-[11px] font-bold text-amber-400">✗ Restricted Symbol</div>
              <div className="text-[10px] text-slate-400 font-mono">TSLA 5 @ $100</div>
            </button>

            <button
              type="button"
              onClick={() => applyPreset('AAPL', 'BUY', 1, '60000.00')}
              className="px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-left border border-slate-700/50 transition-colors"
            >
              <div className="text-[11px] font-bold text-rose-400">✗ Fat-Finger Price</div>
              <div className="text-[10px] text-slate-400 font-mono">AAPL 1 @ $60,000</div>
            </button>

            <button
              type="button"
              onClick={() => applyPreset('MSFT', 'BUY', 100, '250.00')}
              className="px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-left border border-slate-700/50 transition-colors"
            >
              <div className="text-[11px] font-bold text-rose-400">✗ Exceeds Max Value</div>
              <div className="text-[10px] text-slate-400 font-mono">MSFT ($25,000)</div>
            </button>

            <button
              type="button"
              onClick={() => applyPreset('NVDA', 'SELL', 10, '120.00')}
              className="px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-left border border-slate-700/50 transition-colors"
            >
              <div className="text-[11px] font-bold text-emerald-400">✓ Valid Sell</div>
              <div className="text-[10px] text-slate-400 font-mono">NVDA 10 @ $120</div>
            </button>
          </div>
        </div>

        {formError && (
          <div className="mb-4 p-3 rounded-xl bg-rose-950/40 border border-rose-800/80 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{formError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Side Toggle BUY vs SELL */}
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">
              Order Side
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleSideChange('BUY')}
                className={`py-2.5 rounded-xl font-bold text-xs tracking-wider uppercase transition-all flex items-center justify-center gap-1.5 border ${
                  side === 'BUY'
                    ? 'bg-emerald-600 text-white border-emerald-500 shadow-lg shadow-emerald-950 ring-1 ring-emerald-400/40'
                    : 'bg-slate-900/80 text-slate-400 border-slate-800 hover:bg-slate-800'
                }`}
              >
                <TrendingUp className="w-4 h-4" />
                BUY
              </button>
              <button
                type="button"
                onClick={() => handleSideChange('SELL')}
                className={`py-2.5 rounded-xl font-bold text-xs tracking-wider uppercase transition-all flex items-center justify-center gap-1.5 border ${
                  side === 'SELL'
                    ? 'bg-rose-600 text-white border-rose-500 shadow-lg shadow-rose-950 ring-1 ring-rose-400/40'
                    : 'bg-slate-900/80 text-slate-400 border-slate-800 hover:bg-slate-800'
                }`}
              >
                <TrendingDown className="w-4 h-4" />
                SELL
              </button>
            </div>
          </div>

          {/* Symbol */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Asset Symbol (Ticker)
              </label>
              <div className="flex gap-1">
                {['AAPL', 'MSFT', 'NVDA', 'TSLA'].map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => handleSymbolChange(s)}
                    className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
            <input
              type="text"
              value={symbol}
              onChange={(e) => handleSymbolChange(e.target.value)}
              placeholder="e.g. AAPL"
              maxLength={10}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 font-mono text-sm tracking-wide focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 uppercase"
              required
            />
          </div>

          {/* Quantity & Quick Increments */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Order Quantity (Shares)
              </label>
              <div className="flex gap-1">
                {[10, 50, 100, 500].map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => {
                      setQuantity(q);
                      notifyChange(symbol, side, q, price);
                    }}
                    className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    +{q}
                  </button>
                ))}
              </div>
            </div>
            <input
              type="number"
              min={1}
              step={1}
              value={quantity}
              onChange={(e) => handleQuantityChange(e.target.value)}
              placeholder="10"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50"
              required
            />
          </div>

          {/* Limit Price */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Limit Price per Share (USD)
              </label>
              <div className="flex gap-1">
                {['0.01', '10.00', '150.00'].map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => {
                      setPrice(p);
                      notifyChange(symbol, side, quantity, p);
                    }}
                    className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    ${p}
                  </button>
                ))}
              </div>
            </div>
            <div className="relative">
              <span className="absolute left-3.5 top-2.5 text-slate-400 font-mono text-sm">
                $
              </span>
              <input
                type="number"
                min="0.0001"
                step="any"
                value={price}
                onChange={(e) => handlePriceChange(e.target.value)}
                placeholder="150.00"
                className="w-full pl-8 pr-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50"
                required
              />
            </div>
          </div>

          {/* Total Value Bar */}
          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Estimated Order Value</span>
            <span className="text-base font-bold font-mono text-emerald-400">
              {formatCurrency(orderValue)}
            </span>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className={`w-full py-3.5 rounded-xl font-bold text-sm tracking-wide uppercase transition-all flex items-center justify-center gap-2 shadow-lg disabled:opacity-50 ${
              side === 'BUY'
                ? 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-emerald-950/60 ring-1 ring-emerald-400/30'
                : 'bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white shadow-rose-950/60 ring-1 ring-rose-400/30'
            }`}
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Evaluating Risk Rules...
              </span>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Submit {side} Order for Validation
              </>
            )}
          </button>
        </form>
      </div>

      <div className="text-[11px] text-slate-500 text-center mt-4">
        Orders undergo 9 synchronous deterministic pre-trade risk checks before approval
      </div>
    </div>
  );
};
