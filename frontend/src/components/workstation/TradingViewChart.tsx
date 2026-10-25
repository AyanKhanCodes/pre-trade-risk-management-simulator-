import React, { useEffect, useRef } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time, CandlestickSeries } from 'lightweight-charts';
import { Candle, Quote } from '../../types';

interface TradingViewChartProps {
  symbol: string;
  candles: Candle[];
  latestQuote: Quote | null;
  interval: string;
  onIntervalChange: (interval: string) => void;
}

export const TradingViewChart: React.FC<TradingViewChartProps> = ({
  symbol,
  candles,
  latestQuote,
  interval,
  onIntervalChange,
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#0b101b' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
      timeScale: {
        borderColor: '#334155',
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: '#334155',
      },
      width: chartContainerRef.current.clientWidth,
      height: 420,
    });

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#f43f5e',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#f43f5e',
    });

    chartRef.current = chart;
    seriesRef.current = candlestickSeries;

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  // Update candle data
  useEffect(() => {
    if (!seriesRef.current || candles.length === 0) return;

    const formattedData: CandlestickData<Time>[] = candles
      .map((c) => ({
        time: (new Date(c.timestamp).getTime() / 1000) as Time,
        open: parseFloat(c.open),
        high: parseFloat(c.high),
        low: parseFloat(c.low),
        close: parseFloat(c.close),
      }))
      .sort((a, b) => (a.time as number) - (b.time as number));

    seriesRef.current.setData(formattedData);
    chartRef.current?.timeScale().fitContent();
  }, [candles]);

  // Update live tick onto latest candle
  useEffect(() => {
    if (!seriesRef.current || !latestQuote || latestQuote.symbol !== symbol) return;

    const price = parseFloat(latestQuote.ltp);
    const tickTime = (new Date(latestQuote.timestamp).getTime() / 1000) as Time;

    seriesRef.current.update({
      time: tickTime,
      open: parseFloat(latestQuote.open),
      high: Math.max(parseFloat(latestQuote.high), price),
      low: Math.min(parseFloat(latestQuote.low), price),
      close: price,
    });
  }, [latestQuote, symbol]);

  return (
    <div className="bg-[#0b101b] border border-slate-800 rounded-2xl p-4 shadow-xl flex flex-col">
      <div className="flex items-center justify-between pb-3 mb-2 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="flex items-baseline gap-2">
            <h2 className="text-xl font-bold tracking-tight text-white">{symbol}</h2>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/50">
              NSE Cash
            </span>
          </div>
          {latestQuote && (
            <div className="flex items-baseline gap-2 ml-2">
              <span className="text-xl font-mono font-bold text-white">
                ₹{parseFloat(latestQuote.ltp).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span
                className={`text-xs font-mono font-semibold ${
                  parseFloat(latestQuote.change) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {parseFloat(latestQuote.change) >= 0 ? '+' : ''}
                {latestQuote.change} ({latestQuote.change_pct}%)
              </span>
            </div>
          )}
        </div>

        {/* Timeframe selector */}
        <div className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-lg border border-slate-800">
          {['1m', '5m', '1D'].map((tf) => (
            <button
              key={tf}
              onClick={() => onIntervalChange(tf)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                interval === tf
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      <div ref={chartContainerRef} className="w-full relative" />
    </div>
  );
};
