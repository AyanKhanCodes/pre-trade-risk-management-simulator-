import React, { useState } from 'react';
import {
  Sliders,
  Check,
  Edit2,
  X,
  Shield,
  Layers,
  AlertCircle
} from 'lucide-react';
import { RiskRule, RiskConfigUpdateRequest } from '../../types';
import { formatCurrency, formatNumber, getCategoryColor } from '../../lib/utils';

interface RiskRuleCardProps {
  rule: RiskRule;
  onUpdateConfig: (updates: RiskConfigUpdateRequest) => Promise<void>;
}

export const RiskRuleCard: React.FC<RiskRuleCardProps> = ({ rule, onUpdateConfig }) => {
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editValue, setEditValue] = useState<string>(rule.current_value || '');
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const categoryStyle = getCategoryColor(rule.category);

  const handleStartEdit = () => {
    setEditValue(rule.current_value || '');
    setError(null);
    setIsEditing(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setError(null);
  };

  const handleSave = async () => {
    if (!rule.config_key) return;

    setError(null);
    setIsSaving(true);

    try {
      const updates: RiskConfigUpdateRequest = {};

      if (rule.config_key === 'restricted_symbols') {
        const symbols = editValue
          .split(',')
          .map((s) => s.trim().toUpperCase())
          .filter((s) => s.length > 0);
        updates.restricted_symbols = symbols;
      } else if (
        rule.config_key === 'max_order_value' ||
        rule.config_key === 'min_price' ||
        rule.config_key === 'max_price' ||
        rule.config_key === 'max_daily_notional'
      ) {
        const val = parseFloat(editValue);
        if (isNaN(val) || val <= 0) {
          throw new Error('Must be a valid positive number');
        }
        updates[rule.config_key] = editValue;
      } else if (
        rule.config_key === 'max_quantity' ||
        rule.config_key === 'max_daily_orders'
      ) {
        const val = parseInt(editValue, 10);
        if (isNaN(val) || val <= 0) {
          throw new Error('Must be a valid positive integer');
        }
        updates[rule.config_key] = val;
      }

      await onUpdateConfig(updates);
      setIsEditing(false);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to update rule threshold.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const formatDisplayValue = (configKey: string, val: string | null) => {
    if (!val) return 'Built-in Hardcoded Rule';
    if (
      configKey === 'max_order_value' ||
      configKey === 'min_price' ||
      configKey === 'max_price' ||
      configKey === 'max_daily_notional'
    ) {
      return formatCurrency(val);
    }
    if (configKey === 'max_quantity' || configKey === 'max_daily_orders') {
      return `${formatNumber(val)} units`;
    }
    return val;
  };

  return (
    <div className="rounded-2xl bg-[#0f1626] border border-slate-800 p-5 shadow-xl flex flex-col justify-between hover:border-slate-700/80 transition-all">
      <div>
        {/* Top Badges */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/60">
            {rule.rule_id}
          </span>
          <span
            className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${categoryStyle.bg} ${categoryStyle.text} ${categoryStyle.border}`}
          >
            {rule.category}
          </span>
        </div>

        {/* Rule Title */}
        <h3 className="text-sm font-bold text-slate-100 mb-1.5 flex items-center gap-1.5">
          {rule.name}
        </h3>

        {/* Description */}
        <p className="text-xs text-slate-400 leading-relaxed mb-4">
          {rule.description}
        </p>

        {error && (
          <div className="mb-3 p-2 rounded-lg bg-rose-950/40 border border-rose-800/80 text-rose-300 text-[11px] flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Threshold / Edit Section */}
      <div className="pt-3 border-t border-slate-800/80">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[11px] font-semibold text-slate-400">
            Enforced Threshold:
          </span>
          {rule.config_key && !isEditing && (
            <button
              onClick={handleStartEdit}
              className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-medium"
            >
              <Edit2 className="w-3 h-3" />
              Configure
            </button>
          )}
        </div>

        {isEditing ? (
          <div className="space-y-2 mt-2">
            <div>
              <input
                type="text"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                placeholder={rule.config_key === 'restricted_symbols' ? 'e.g. YESBANK, SUZLON, IDEA' : 'Enter value'}
                className="w-full px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs font-mono text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                autoFocus
              />
              <span className="text-[10px] text-slate-500 block mt-0.5">
                {rule.config_key === 'restricted_symbols'
                  ? 'Comma-separated ticker list'
                  : 'Numeric limit parameter'}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1 transition-colors disabled:opacity-50"
              >
                <Check className="w-3.5 h-3.5" />
                {isSaving ? 'Saving...' : 'Apply'}
              </button>
              <button
                onClick={handleCancel}
                disabled={isSaving}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
              >
                <X className="w-3.5 h-3.5" />
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
            <span className="font-mono text-xs font-bold text-slate-200">
              {formatDisplayValue(rule.config_key, rule.current_value)}
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Active Enforcer
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
