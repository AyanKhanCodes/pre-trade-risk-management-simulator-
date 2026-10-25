import React, { useState, useMemo } from 'react';
import {
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Eye,
  ArrowUpDown,
  History,
  TrendingUp,
  TrendingDown,
  RefreshCw
} from 'lucide-react';
import { Order, OrderSide, OrderStatus } from '../../types';
import { formatCurrency, formatDateTime, formatNumber } from '../../lib/utils';
import { OrderDetailModal } from './OrderDetailModal';

interface OrderHistoryTableProps {
  orders: Order[];
  isLoading: boolean;
  onRefresh: () => void;
}

export const OrderHistoryTable: React.FC<OrderHistoryTableProps> = ({
  orders,
  isLoading,
  onRefresh,
}) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | OrderStatus>('ALL');
  const [sideFilter, setSideFilter] = useState<'ALL' | OrderSide>('ALL');
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  const filteredOrders = useMemo(() => {
    return orders.filter((o) => {
      if (searchTerm && !o.symbol.toLowerCase().includes(searchTerm.toLowerCase().trim())) {
        return false;
      }
      if (statusFilter !== 'ALL' && o.status !== statusFilter) {
        return false;
      }
      if (sideFilter !== 'ALL' && o.side !== sideFilter) {
        return false;
      }
      return true;
    });
  }, [orders, searchTerm, statusFilter, sideFilter]);

  return (
    <div className="space-y-4">
      {/* Table Header & Controls */}
      <div className="rounded-2xl bg-[#0f1626] border border-slate-800 p-4 shadow-xl">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <History className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 tracking-tight">
                Audit Trail & Order Ledger
              </h2>
              <p className="text-[11px] text-slate-400">
                Persistent immutable record of all submitted simulated orders and risk decisions
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors text-xs font-medium flex items-center gap-1.5 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-emerald-400' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Filter Toolbar */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4 pt-4 border-t border-slate-800/80">
          {/* Symbol Search */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search ticker (e.g. RELIANCE, TCS)..."
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400 shrink-0 font-medium">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as 'ALL' | OrderStatus)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
            >
              <option value="ALL">All Statuses ({orders.length})</option>
              <option value="APPROVED">Approved Orders</option>
              <option value="REJECTED">Rejected Orders</option>
            </select>
          </div>

          {/* Side Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400 shrink-0 font-medium">Side:</span>
            <select
              value={sideFilter}
              onChange={(e) => setSideFilter(e.target.value as 'ALL' | OrderSide)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
            >
              <option value="ALL">All Sides</option>
              <option value="BUY">BUY Only</option>
              <option value="SELL">SELL Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div className="rounded-2xl bg-[#0f1626] border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/60 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                <th className="py-3.5 px-4">Timestamp (UTC)</th>
                <th className="py-3.5 px-4">Symbol</th>
                <th className="py-3.5 px-4">Side</th>
                <th className="py-3.5 px-4 text-right">Quantity</th>
                <th className="py-3.5 px-4 text-right">Price</th>
                <th className="py-3.5 px-4 text-right">Total Notional</th>
                <th className="py-3.5 px-4 text-center">Risk Verdict</th>
                <th className="py-3.5 px-4 text-center">Audit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs">
              {isLoading && orders.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
                    <div className="flex items-center justify-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-emerald-400" />
                      <span>Loading order history ledger...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
                    <div className="max-w-xs mx-auto space-y-2">
                      <History className="w-8 h-8 mx-auto text-slate-600" />
                      <p className="font-semibold text-slate-300">No orders match criteria</p>
                      <p className="text-[11px] text-slate-500">
                        Try clearing search filters or execute a new simulated trade from the Order Execution tab.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredOrders.map((order) => {
                  const isApproved = order.status === 'APPROVED';
                  return (
                    <tr
                      key={order.order_id}
                      onClick={() => setSelectedOrder(order)}
                      className="hover:bg-slate-800/40 cursor-pointer transition-colors group"
                    >
                      <td className="py-3.5 px-4 font-mono text-slate-400 text-[11px] whitespace-nowrap">
                        {formatDateTime(order.created_at)}
                      </td>
                      <td className="py-3.5 px-4 font-bold font-mono text-slate-100 text-sm">
                        {order.symbol}
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            order.side === 'BUY'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}
                        >
                          {order.side === 'BUY' ? (
                            <TrendingUp className="w-3 h-3" />
                          ) : (
                            <TrendingDown className="w-3 h-3" />
                          )}
                          {order.side}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono text-slate-200">
                        {formatNumber(order.quantity)}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono text-slate-200">
                        {formatCurrency(order.price)}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-bold text-slate-100">
                        {formatCurrency(order.order_value)}
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                            isApproved
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                          }`}
                        >
                          {isApproved ? (
                            <CheckCircle2 className="w-3 h-3" />
                          ) : (
                            <XCircle className="w-3 h-3" />
                          )}
                          {order.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedOrder(order);
                          }}
                          className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors text-xs font-medium inline-flex items-center gap-1"
                        >
                          <Eye className="w-3 h-3" />
                          Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Table Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-900/50 flex items-center justify-between text-xs text-slate-500 px-4">
          <span>
            Showing {filteredOrders.length} of {orders.length} orders
          </span>
          <span className="font-mono text-[11px]">
            Audited via aiosqlite SQLite Engine
          </span>
        </div>
      </div>

      {/* Selected Order Detail Dossier Modal */}
      {selectedOrder && (
        <OrderDetailModal
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
        />
      )}
    </div>
  );
};
