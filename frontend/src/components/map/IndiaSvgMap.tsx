import React, { useState } from 'react';
import { StateMapMetric } from '../../types';
import { INDIA_SVG_FEATURES, StateSvgFeature } from './indiaMapData';
import clsx from 'clsx';
import { ShieldAlert, IndianRupee, Activity, MapPin } from 'lucide-react';

interface IndiaSvgMapProps {
  metrics: StateMapMetric[];
  selectedState: string | null;
  onSelectState: (stateName: string) => void;
  metricType?: 'alerts' | 'sanctioned' | 'utilization';
}

export const IndiaSvgMap: React.FC<IndiaSvgMapProps> = ({
  metrics,
  selectedState,
  onSelectState,
  metricType = 'alerts',
}) => {
  const [hoveredFeature, setHoveredFeature] = useState<StateSvgFeature | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);

  // Map metric lookup by state name (case-insensitive)
  const metricMap = React.useMemo(() => {
    const map = new Map<string, StateMapMetric>();
    metrics.forEach((m) => {
      map.set(m.state_name.toLowerCase().trim(), m);
    });
    return map;
  }, [metrics]);

  const getStateMetric = (name: string, rawName: string): StateMapMetric | undefined => {
    return (
      metricMap.get(name.toLowerCase().trim()) ||
      metricMap.get(rawName.toLowerCase().trim())
    );
  };

  // Determine choropleth fill color
  const getFillColor = (feature: StateSvgFeature, isSelected: boolean, isHovered: boolean): string => {
    const metric = getStateMetric(feature.name, feature.raw_name);

    if (isSelected) {
      return '#38BDF8'; // Sky-400 for selected
    }
    if (isHovered) {
      return '#60A5FA'; // Blue-400 on hover
    }

    if (!metric) {
      return '#1E293B'; // Slate-800 default
    }

    if (metricType === 'alerts') {
      if (metric.critical_alerts > 0) return '#EF4444'; // Red-500
      if (metric.high_alerts > 5) return '#F97316'; // Orange-500
      if (metric.medium_alerts > 10) return '#F59E0B'; // Amber-500
      return '#10B981'; // Emerald-500
    }

    if (metricType === 'utilization') {
      const u = metric.utilization_pct;
      if (u >= 75) return '#10B981'; // Emerald-500
      if (u >= 50) return '#0EA5E9'; // Sky-500
      if (u >= 25) return '#F59E0B'; // Amber-500
      return '#EF4444'; // Red-500
    }

    // Sanctioned amount
    const amt = metric.sanctioned_amount_cr;
    if (amt > 2000) return '#0284C7';
    if (amt > 1000) return '#0369A1';
    if (amt > 300) return '#075985';
    return '#1E293B';
  };

  const hoveredMetric = hoveredFeature
    ? getStateMetric(hoveredFeature.name, hoveredFeature.raw_name)
    : null;

  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center p-2 select-none">
      <svg
        viewBox="0 0 600 680"
        className="w-full h-auto max-h-[560px] drop-shadow-2xl transition-all"
        style={{ filter: 'drop-shadow(0 10px 25px rgba(0, 0, 0, 0.5))' }}
      >
        <defs>
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        <g>
          {INDIA_SVG_FEATURES.map((feature) => {
            const isSelected =
              selectedState?.toLowerCase().trim() === feature.name.toLowerCase().trim() ||
              selectedState?.toLowerCase().trim() === feature.raw_name.toLowerCase().trim();
            const isHovered = hoveredFeature?.id === feature.id;
            const fill = getFillColor(feature, isSelected, isHovered);

            return (
              <path
                key={feature.id}
                data-id={feature.id}
                data-state={feature.name}
                d={feature.d}
                fill={fill}
                stroke={isSelected ? '#FFFFFF' : '#0F172A'}
                strokeWidth={isSelected ? 2.5 : 1}
                filter={isSelected ? 'url(#glow)' : undefined}
                className={clsx(
                  'transition-all duration-200 cursor-pointer',
                  isHovered && 'brightness-125'
                )}
                onMouseEnter={(e) => {
                  setHoveredFeature(feature);
                  const rect = e.currentTarget.ownerSVGElement?.getBoundingClientRect();
                  if (rect) {
                    setTooltipPos({
                      x: e.clientX - rect.left,
                      y: e.clientY - rect.top,
                    });
                  }
                }}
                onMouseMove={(e) => {
                  const rect = e.currentTarget.ownerSVGElement?.getBoundingClientRect();
                  if (rect) {
                    setTooltipPos({
                      x: e.clientX - rect.left,
                      y: e.clientY - rect.top,
                    });
                  }
                }}
                onMouseLeave={() => {
                  setHoveredFeature(null);
                  setTooltipPos(null);
                }}
                onClick={() => onSelectState(feature.name)}
              />
            );
          })}
        </g>
      </svg>

      {/* Floating Hover Tooltip */}
      {hoveredFeature && tooltipPos && (
        <div
          className="absolute z-30 pointer-events-none bg-[#0F172A]/95 border border-sky-500/50 rounded-xl p-3 shadow-2xl backdrop-blur-md min-w-[200px] text-xs transform -translate-x-1/2 -translate-y-full mb-3"
          style={{
            left: Math.max(100, Math.min(500, tooltipPos.x)),
            top: Math.max(70, tooltipPos.y),
          }}
        >
          <div className="flex items-center justify-between pb-1.5 border-b border-slate-800">
            <span className="font-bold text-white tracking-wide">{hoveredFeature.name}</span>
            <span className="text-[10px] font-mono text-sky-400">Click to Inspect →</span>
          </div>

          {hoveredMetric ? (
            <div className="pt-2 space-y-1.5 font-mono text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-400">Total Works:</span>
                <span className="text-slate-200 font-semibold">{hoveredMetric.total_works.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Sanctioned:</span>
                <span className="text-emerald-400 font-semibold">₹{hoveredMetric.sanctioned_amount_cr} Cr</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Disbursed:</span>
                <span className="text-slate-300">₹{hoveredMetric.disbursed_amount_cr} Cr</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Utilization:</span>
                <span className="text-sky-300 font-semibold">{hoveredMetric.utilization_pct}%</span>
              </div>
              {hoveredMetric.critical_alerts > 0 && (
                <div className="flex justify-between text-red-400 font-bold pt-1 border-t border-slate-800">
                  <span>Critical Alerts:</span>
                  <span>{hoveredMetric.critical_alerts}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="pt-2 text-slate-500 font-mono text-[11px]">
              No local data cached for this territory.
            </div>
          )}
        </div>
      )}

      {/* Map Legend */}
      <div className="mt-2 w-full max-w-lg bg-[#0B1120]/90 border border-slate-800/80 rounded-xl px-4 py-2 flex items-center justify-between text-[10px] font-mono text-slate-400 backdrop-blur-sm">
        <span className="uppercase text-slate-500 font-bold">Choropleth Radar:</span>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" />
            <span>Critical Breaches</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
            <span>Moderate Risk</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
            <span>Optimal / Normal</span>
          </div>
        </div>
      </div>
    </div>
  );
};
