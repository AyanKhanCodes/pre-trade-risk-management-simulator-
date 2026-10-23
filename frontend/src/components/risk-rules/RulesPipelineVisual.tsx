import React from 'react';
import {
  ArrowRight,
  Shield,
  Layers,
  Cpu,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Lock,
  Workflow,
  AlertTriangle
} from 'lucide-react';

export const RulesPipelineVisual: React.FC = () => {
  const stages = [
    {
      step: '01',
      title: 'Order Ingestion',
      state: 'CREATED',
      desc: 'Parses payload, validates types & bounds, assigns unique UUID.',
      rules: ['Pydantic Schema', 'Format Validation'],
      color: 'border-blue-500/40 bg-blue-950/20 text-blue-400',
    },
    {
      step: '02',
      title: 'Price Controls',
      state: 'VALIDATING',
      desc: 'Guards against sub-penny stocks and unintended price spikes.',
      rules: ['RISK-05 Penny Stock ($1.00 min)', 'RISK-07 Fat-Finger ($50k max)'],
      color: 'border-purple-500/40 bg-purple-950/20 text-purple-400',
    },
    {
      step: '03',
      title: 'Position Limits',
      state: 'VALIDATING',
      desc: 'Prevents single-order over-concentration & excessive capital risk.',
      rules: ['RISK-01 Max Value ($10,000)', 'RISK-06 Max Quantity (10,000 shares)'],
      color: 'border-emerald-500/40 bg-emerald-950/20 text-emerald-400',
    },
    {
      step: '04',
      title: 'Compliance Gate',
      state: 'VALIDATING',
      desc: 'Blocks securities restricted by regulatory or internal blacklists.',
      rules: ['RISK-02 Restricted Symbols (TSLA, GME, AMC)'],
      color: 'border-amber-500/40 bg-amber-950/20 text-amber-400',
    },
    {
      step: '05',
      title: 'Portfolio & Activity',
      state: 'VALIDATING',
      desc: 'Calculates day-to-date aggregates to enforce cumulative caps.',
      rules: ['RISK-08 Daily Order Count (50)', 'RISK-09 Daily Notional ($500k)'],
      color: 'border-cyan-500/40 bg-cyan-950/20 text-cyan-400',
    },
    {
      step: '06',
      title: 'Verdict & State Machine',
      state: 'APPROVED / REJECTED',
      desc: 'If all pass: APPROVED. If any fail: REJECTED with all violation reasons.',
      rules: ['Atomic State Transition', 'aiosqlite Persistence'],
      color: 'border-emerald-500/60 bg-emerald-950/30 text-emerald-300',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Visual Pipeline Flow */}
      <div className="rounded-2xl bg-[#0f1626] border border-slate-800 p-6 shadow-xl">
        <div className="flex items-center gap-2.5 mb-2">
          <Workflow className="w-5 h-5 text-emerald-400" />
          <h3 className="text-base font-bold text-slate-100 tracking-tight">
            Deterministic Pre-Trade Risk Pipeline Architecture
          </h3>
        </div>
        <p className="text-xs text-slate-400 mb-6">
          Every simulated order passes through 5 sequential inspection gates before reaching the matching engine.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 relative">
          {stages.map((stage, idx) => (
            <div
              key={stage.step}
              className={`p-4 rounded-xl border flex flex-col justify-between transition-all ${stage.color}`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-900/80 border border-slate-800">
                    STAGE {stage.step}
                  </span>
                  <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-slate-900/60 text-slate-400">
                    {stage.state}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-100 mb-1">{stage.title}</h4>
                <p className="text-[11px] text-slate-400 leading-relaxed mb-3">
                  {stage.desc}
                </p>
              </div>

              <div className="pt-2.5 border-t border-slate-800/60 space-y-1">
                {stage.rules.map((rule, rIdx) => (
                  <div key={rIdx} className="text-[10px] font-mono text-slate-300 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                    <span className="truncate">{rule}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Professor Academic / Trading Logic Explanations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-5 rounded-2xl bg-[#0f1626] border border-slate-800">
          <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2 mb-2">
            <Cpu className="w-4 h-4 text-emerald-400" />
            Why Non-Short-Circuiting Evaluation?
          </h4>
          <p className="text-xs text-slate-400 leading-relaxed">
            In enterprise institutional trading (e.g., FIX 4.2 / OUCH protocol gateways), rejecting an order on the first failed check forces the trader to submit repeatedly to discover other violations. Our engine executes <strong>all 9 checks simultaneously</strong>, accumulating every failing condition so the trader or algorithm receives an exhaustive audit diagnostic in a single response.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-[#0f1626] border border-slate-800">
          <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2 mb-2">
            <Lock className="w-4 h-4 text-purple-400" />
            Penny Stock & Microcap Protection
          </h4>
          <p className="text-xs text-slate-400 leading-relaxed">
            As requested by trading faculty, prices such as <strong>$0.01</strong> represent extreme microcap volatility, illiquidity, and potential market manipulation (pump-and-dump). <strong>RISK-05</strong> enforces a configurable minimum price threshold (default $1.00), preventing accidental trades in sub-dollar instruments.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-[#0f1626] border border-slate-800">
          <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Anti-Erroneous / Fat-Finger Filtering
          </h4>
          <p className="text-xs text-slate-400 leading-relaxed">
            A trader intending to enter $150.00 might type $15,000 or $50,000. <strong>RISK-07</strong> rejects abnormally elevated prices, while <strong>RISK-01</strong> caps maximum order notional value. This prevents catastrophic market-impact trades from ever reaching the execution ledger.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-[#0f1626] border border-slate-800">
          <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2 mb-2">
            <Layers className="w-4 h-4 text-blue-400" />
            Finite State Machine Invariants
          </h4>
          <p className="text-xs text-slate-400 leading-relaxed">
            Order lifecycle strictly adheres to: <br />
            <code className="text-emerald-400 font-mono text-[11px]">CREATED → VALIDATING → APPROVED (or REJECTED)</code>.
            Illegal transitions (e.g. attempting to execute a rejected order or re-approving an executed order) are prevented by domain exceptions verified by property-based unit tests.
          </p>
        </div>
      </div>
    </div>
  );
};
