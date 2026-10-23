import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  CartesianGrid
} from 'recharts';
import { OrderStatsSummary } from '../../types';

interface ApprovalRateChartProps {
  stats: OrderStatsSummary | null;
}

export const ApprovalRateChart: React.FC<ApprovalRateChartProps> = ({ stats }) => {
  if (!stats) return null;

  const data = [
    {
      period: "Today's Session",
      Approved: stats.today.approved,
      Rejected: stats.today.rejected,
    },
    {
      period: 'All-Time Total',
      Approved: stats.all_time.approved,
      Rejected: stats.all_time.rejected,
    },
  ];

  return (
    <div className="rounded-2xl bg-[#0f1626] border border-slate-800 p-5 shadow-xl">
      <h3 className="text-sm font-bold text-slate-100 mb-1">
        Order Decisions: Approved vs Rejected
      </h3>
      <p className="text-xs text-slate-400 mb-4">
        Comparison of passed compliance checks versus blocked risky orders
      </p>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis dataKey="period" stroke="#64748b" fontSize={11} tickLine={false} />
            <YAxis stroke="#64748b" fontSize={11} tickLine={false} allowDecimals={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '0.75rem',
                fontSize: '12px',
                color: '#f8fafc',
              }}
            />
            <Legend
              wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
              iconType="circle"
            />
            <Bar dataKey="Approved" fill="#10b981" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Rejected" fill="#f43f5e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
