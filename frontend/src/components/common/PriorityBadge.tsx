import React from 'react';
import { PriorityTier } from '../../types';
import clsx from 'clsx';

interface PriorityBadgeProps {
  priority: PriorityTier | string;
  size?: 'sm' | 'md' | 'lg';
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority, size = 'md' }) => {
  const p = (priority || 'LOW').toUpperCase();

  const styles: Record<string, string> = {
    CRITICAL: 'bg-red-500/15 text-red-400 border-red-500/40 hover:bg-red-500/25',
    HIGH: 'bg-amber-500/15 text-amber-400 border-amber-500/40 hover:bg-amber-500/25',
    MEDIUM: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/40 hover:bg-yellow-500/25',
    LOW: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40 hover:bg-emerald-500/25',
    NORMAL: 'bg-slate-500/15 text-slate-300 border-slate-500/40 hover:bg-slate-500/25',
  };

  const sizes = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3.5 py-1.5',
  };

  const badgeClass = styles[p] || styles.LOW;

  return (
    <span
      className={clsx(
        'inline-flex items-center font-semibold rounded-full border tracking-wide uppercase font-mono transition-colors shadow-sm',
        badgeClass,
        sizes[size]
      )}
    >
      <span className={clsx('w-1.5 h-1.5 rounded-full mr-1.5', {
        'bg-red-400 animate-pulse': p === 'CRITICAL',
        'bg-amber-400': p === 'HIGH',
        'bg-yellow-300': p === 'MEDIUM',
        'bg-emerald-400': p === 'LOW' || p === 'NORMAL',
      })} />
      {p}
    </span>
  );
};
