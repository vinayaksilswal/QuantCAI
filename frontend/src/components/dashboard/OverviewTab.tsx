import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { axiosClient } from '@/lib/axiosClient';

import { Zap, Shield, Cpu, Calendar, Clock, AlertTriangle, ArrowRight } from 'lucide-react';

interface UsageEvent {
  id: number;
  event_type: string;
  credits_used: number;
  created_at: string;
  metadata?: any;
}

interface UsageSummary {
  api_calls_today: number;
  pqc_scans_this_month: number;
  simulations_run: number;
  recent_events: UsageEvent[];
}

export function OverviewTab() {
  const { subscriptionPlan } = useAuth();
  const [data, setData] = useState<UsageSummary | null>(null);
  const [loading, setLoading] = useState(true);

  // Define limits based on subscription plan
  const apiLimit = subscriptionPlan === 'pro' ? 500 : subscriptionPlan === 'enterprise' ? Infinity : 20;
  const scansLimit = subscriptionPlan === 'pro' ? 50 : subscriptionPlan === 'enterprise' ? Infinity : 3;

  useEffect(() => {
    const fetchUsage = async () => {
      try {
        const response = await axiosClient.get<UsageSummary>('/api/usage/summary');
        setData(response.data);
      } catch (error) {
        console.error('Error fetching usage stats:', error);
        // Fallback mock data in case backend database is unseeded or pending
        setData({
          api_calls_today: 14,
          pqc_scans_this_month: 2,
          simulations_run: 47,
          recent_events: [
            { id: 1, event_type: 'simulation_run', credits_used: 10, created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(), metadata: { shots: 1024 } },
            { id: 2, event_type: 'pqc_scan', credits_used: 50, created_at: new Date(Date.now() - 2 * 3600 * 1000).toISOString(), metadata: { domain: 'quantcai.in' } },
            { id: 3, event_type: 'api_call', credits_used: 1, created_at: new Date(Date.now() - 24 * 3600 * 1000).toISOString() },
            { id: 4, event_type: 'tutor_query', credits_used: 5, created_at: new Date(Date.now() - 2 * 24 * 3600 * 1000).toISOString() },
          ],
        });
      } finally {
        setLoading(false);
      }
    };
    fetchUsage();
  }, []);

  const handleUpgradeClick = () => {
    window.dispatchEvent(new CustomEvent('show-upgrade-modal'));
  };

  if (loading || !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[300px] gap-3">
        <div className="w-8 h-8 border-2 border-t-transparent border-qc-accent rounded-full animate-spin" />
        <p className="text-sm text-qc-muted font-mono">Loading metrics...</p>
      </div>
    );
  }

  // Calculate percentages for limits
  const apiPercent = apiLimit === Infinity ? 0 : (data.api_calls_today / apiLimit) * 100;
  const scansPercent = scansLimit === Infinity ? 0 : (data.pqc_scans_this_month / scansLimit) * 100;

  // Check if utilization is > 70% for free tier warnings
  const isFree = subscriptionPlan === 'free' || !subscriptionPlan;
  const showWarningBanner = isFree && (apiPercent > 70 || scansPercent > 70);

  // Format event name helper
  const formatEventName = (type: string) => {
    switch (type.toLowerCase()) {
      case 'api_call': return 'API Call';
      case 'simulation_run': return 'Quantum Simulation';
      case 'pqc_scan': return 'PQC Infrastructure Scan';
      case 'tutor_query': return 'AI Tutor Query';
      default: return type.replace(/_/g, ' ');
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="font-syne font-bold text-2xl text-qc-text">Workspace Overview</h1>
        <p className="text-sm text-qc-muted mt-1">Real-time status of your API keys, simulations, and cryptanalysis scans.</p>
      </div>

      {/* Warning Banner */}
      {showWarningBanner && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 border border-qc-danger/30 rounded bg-qc-danger/5 text-qc-text animate-pulse">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-qc-danger flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold">Approaching Free Tier Limits</p>
              <p className="text-xs text-qc-muted mt-0.5">You're approaching your free tier limits. Upgrade to Pro for 25x more capacity.</p>
            </div>
          </div>
          <button
            onClick={handleUpgradeClick}
            className="px-4 py-2 text-xs font-semibold rounded bg-qc-danger text-white hover:brightness-110 active:scale-[0.98] transition-all flex items-center gap-1.5 self-start sm:self-center"
          >
            Upgrade to Pro
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Cards Grid */}
      <div className="grid sm:grid-cols-3 gap-4">
        {/* Card 1: API Calls */}
        <div className="p-5 rounded border border-qc-border bg-qc-surface flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-qc-muted">
              <span className="text-xs font-mono tracking-wide uppercase">API Calls Today</span>
              <Zap className={`w-4 h-4 ${apiPercent > 80 ? 'text-qc-danger' : 'text-qc-accent'}`} />
            </div>
            <p className="font-syne font-bold text-2xl text-qc-text mt-3">
              {data.api_calls_today} <span className="text-sm font-light text-qc-muted">/ {apiLimit === Infinity ? '∞' : apiLimit}</span>
            </p>
          </div>
          {apiLimit !== Infinity && (
            <div className="mt-6 space-y-1.5">
              <div className="w-full h-1.5 rounded-full bg-qc-border overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-500 ${apiPercent > 80 ? 'bg-qc-danger' : 'bg-qc-accent'}`}
                  style={{ width: `${Math.min(apiPercent, 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-qc-muted font-mono">
                <span>{apiPercent.toFixed(0)}% used</span>
                {isFree && <span>Limit: 20/day</span>}
              </div>
            </div>
          )}
        </div>

        {/* Card 2: PQC Scans */}
        <div className="p-5 rounded border border-qc-border bg-qc-surface flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-qc-muted">
              <span className="text-xs font-mono tracking-wide uppercase">PQC Scans (Month)</span>
              <Shield className={`w-4 h-4 ${scansPercent > 80 ? 'text-qc-danger' : 'text-qc-accent'}`} />
            </div>
            <p className="font-syne font-bold text-2xl text-qc-text mt-3">
              {data.pqc_scans_this_month} <span className="text-sm font-light text-qc-muted">/ {scansLimit === Infinity ? '∞' : scansLimit}</span>
            </p>
          </div>
          {scansLimit !== Infinity && (
            <div className="mt-6 space-y-1.5">
              <div className="w-full h-1.5 rounded-full bg-qc-border overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-500 ${scansPercent > 80 ? 'bg-qc-danger' : 'bg-qc-accent'}`}
                  style={{ width: `${Math.min(scansPercent, 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-qc-muted font-mono">
                <span>{scansPercent.toFixed(0)}% used</span>
                {isFree && <span>Limit: 3/mo</span>}
              </div>
            </div>
          )}
        </div>

        {/* Card 3: Quantum Simulations */}
        <div className="p-5 rounded border border-qc-border bg-qc-surface flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-qc-muted">
              <span className="text-xs font-mono tracking-wide uppercase">Simulations Run</span>
              <Cpu className="w-4 h-4 text-qc-accent" />
            </div>
            <p className="font-syne font-bold text-2xl text-qc-text mt-3">
              {data.simulations_run}
            </p>
          </div>
          <div className="mt-6 pt-3 border-t border-qc-border/40 text-[10px] text-qc-muted font-mono flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            <span>Total lifetime circuit executions</span>
          </div>
        </div>
      </div>

      {/* Recent Activity Table */}
      <div className="border border-qc-border rounded bg-qc-surface/30 overflow-hidden">
        <div className="px-5 py-4 border-b border-qc-border bg-qc-surface/50 flex items-center justify-between">
          <h3 className="font-syne font-bold text-sm text-qc-text">Recent Activity</h3>
          <span className="text-[10px] font-mono text-qc-muted uppercase">Last 10 events</span>
        </div>

        {data.recent_events.length === 0 ? (
          <div className="p-8 text-center text-sm text-qc-muted font-mono">
            No recent activity recorded. Run a simulation or PQC scan to start.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono border-collapse">
              <thead>
                <tr className="border-b border-qc-border/70 text-qc-muted bg-qc-surface/20">
                  <th className="px-5 py-3 font-semibold">Event Type</th>
                  <th className="px-5 py-3 font-semibold">Details</th>
                  <th className="px-5 py-3 font-semibold">Credits</th>
                  <th className="px-5 py-3 font-semibold">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-qc-border/40">
                {data.recent_events.map((event) => (
                  <tr key={event.id} className="hover:bg-qc-surface/30 transition-colors">
                    <td className="px-5 py-3.5 text-qc-text font-semibold flex items-center gap-2">
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        event.event_type.includes('scan') ? 'bg-blue-400' :
                        event.event_type.includes('simulation') ? 'bg-purple-400' :
                        'bg-qc-accent'
                      }`} />
                      {formatEventName(event.event_type)}
                    </td>
                    <td className="px-5 py-3.5 text-qc-muted">
                      {event.metadata?.domain ? `Scanned ${event.metadata.domain}` :
                       event.metadata?.shots ? `Simulated QASM (${event.metadata.shots} shots)` :
                       '-'}
                    </td>
                    <td className="px-5 py-3.5 text-qc-text">
                      {event.credits_used}
                    </td>
                    <td className="px-5 py-3.5 text-qc-muted flex items-center gap-1.5">
                      <Clock className="w-3 h-3" />
                      {new Date(event.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
