import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend
} from 'recharts';
import { OrderStatsSummary } from '../../types';

interface RejectionPieChartProps {
  stats: OrderStatsSummary | null;
}

export const RejectionPieChart: React.FC<RejectionPieChartProps> = ({ stats }) => {
  if (!stats) return null;

  const total = stats.all_time.total_orders;
  const approved = stats.all_time.approved;
  const rejected = stats.all_time.rejected;

  if (total === 0) {
    return (
      <div className="rounded-2xl bg-[#0f1626] border border-slate-800 p-5 shadow-xl flex flex-col items-center justify-center h-80 text-slate-500 text-xs">
        No orders submitted yet to calculate decision distribution.
      </div>
    );
  }

  const data = [
    { name: 'Approved Orders', value: approved, color: '#10b981' },
    { name: 'Rejected Orders', value: rejected, color: '#f43f5e' },
  ];

  return (
    <div className="rounded-2xl bg-[#0f1626] border border-slate-800 p-5 shadow-xl flex flex-col justify-between">
      <div>
        <h3 className="text-sm font-bold text-slate-100 mb-1">
          Decision Ratio Distribution
        </h3>
        <p className="text-xs text-slate-400 mb-2">
          Portfolio-wide risk engine enforcement efficiency
        </p>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f1626" strokeWidth={2} />
              ))}
            </Pie>
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
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
