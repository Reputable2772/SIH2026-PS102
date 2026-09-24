import React from 'react';
import clsx from 'clsx';
import { ArrowUpRight } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  badge?: string;
  badgeType?: 'danger' | 'warning' | 'success' | 'info';
  className?: string;
  onClick?: () => void;
  clickableHint?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  badge,
  badgeType = 'info',
  className,
  onClick,
  clickableHint,
}) => {
  const badgeStyles = {
    danger: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
    warning: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    success: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    info: 'bg-sky-500/15 text-sky-400 border-sky-500/30',
  };

  return (
    <div
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => (e.key === 'Enter' || e.key === ' ') && onClick() : undefined}
      className={clsx(
        'bg-[#131D31]/90 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 shadow-lg relative overflow-hidden transition-all duration-200 group text-left select-none',
        onClick && 'cursor-pointer hover:border-sky-500/40 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-sky-500/5 focus:outline-none focus:ring-1 focus:ring-sky-500/50',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1 flex items-center space-x-1.5">
            <span>{title}</span>
            {onClick && (
              <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-sky-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all opacity-0 group-hover:opacity-100" />
            )}
          </p>
          <h3 className="text-2xl font-bold text-white tracking-tight font-mono">{value}</h3>
          {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
        </div>
        <div className="p-3 bg-slate-800/70 border border-slate-700/50 rounded-xl text-sky-400 group-hover:scale-105 group-hover:bg-slate-800 group-hover:border-sky-500/30 transition-all">
          {icon}
        </div>
      </div>
      {(badge || clickableHint) && (
        <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between">
          {badge ? (
            <span
              className={clsx(
                'text-[11px] font-medium px-2 py-0.5 rounded border tracking-wide font-mono',
                badgeStyles[badgeType]
              )}
            >
              {badge}
            </span>
          ) : <span />}
          {clickableHint && (
            <span className="text-[10px] text-slate-500 group-hover:text-sky-400 font-mono transition-colors">
              {clickableHint}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
