import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { fetchApi } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';

export interface Entitlements {
  qubits: number;
  depth: number;
  shots: number;
  noise_models: string[];
  ai_chats_daily: number;
  pqc_scans_monthly: number;
  api_requests_daily: number;
  circuit_runs_daily: number;
  custom_cbom: boolean;
  internal_scanning: boolean;
  qpu_priority: boolean;
}

export interface Usage {
  daily_ai_chats: number;
  monthly_pqc_scans: number;
  total_compute_overhead: number;
}

interface SubscriptionContextType {
  tier: 'FREE' | 'PRO' | 'ENTERPRISE';
  cycleResetDate: string;
  usage: Usage;
  limits: Entitlements;
  loading: boolean;
  refreshEntitlements: () => Promise<void>;
}

const defaultLimits: Entitlements = {
  qubits: 3,
  depth: 15,
  shots: 1024,
  noise_models: ['ideal'],
  ai_chats_daily: 10,
  pqc_scans_monthly: 3,
  api_requests_daily: 10,
  circuit_runs_daily: 10,
  custom_cbom: false,
  internal_scanning: false,
  qpu_priority: false,
};

const defaultUsage: Usage = {
  daily_ai_chats: 0,
  monthly_pqc_scans: 0,
  total_compute_overhead: 0.0,
};

const SubscriptionContext = createContext<SubscriptionContextType>({
  tier: 'FREE',
  cycleResetDate: '',
  usage: defaultUsage,
  limits: defaultLimits,
  loading: true,
  refreshEntitlements: async () => {},
});

export const useSubscription = () => useContext(SubscriptionContext);

export const SubscriptionProvider = ({ children }: { children: ReactNode }) => {
  const { user } = useAuth();
  const [tier, setTier] = useState<'FREE' | 'PRO' | 'ENTERPRISE'>('FREE');
  const [cycleResetDate, setCycleResetDate] = useState<string>('');
  const [usage, setUsage] = useState<Usage>(defaultUsage);
  const [limits, setLimits] = useState<Entitlements>(defaultLimits);
  const [loading, setLoading] = useState(true);

  const refreshEntitlements = useCallback(async () => {
    if (!user) {
      setTier('FREE');
      setCycleResetDate('');
      setUsage(defaultUsage);
      setLimits(defaultLimits);
      setLoading(false);
      return;
    }

    try {
      const data = await fetchApi<{
        tier: 'FREE' | 'PRO' | 'ENTERPRISE';
        cycle_reset_date: string;
        usage: Usage;
        limits: Entitlements;
      }>('/api/v1/entitlements');
      
      setTier(data.tier);
      setCycleResetDate(data.cycle_reset_date);
      setUsage(data.usage);
      setLimits(data.limits);
    } catch (err) {
      console.error('Error fetching entitlements:', err);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    refreshEntitlements();
  }, [refreshEntitlements]);

  // Listen for subscription-updated events to refresh entitlements dynamically
  useEffect(() => {
    const handleUpdate = () => {
      refreshEntitlements();
    };
    window.addEventListener('subscription-updated', handleUpdate);
    return () => window.removeEventListener('subscription-updated', handleUpdate);
  }, [refreshEntitlements]);

  return (
    <SubscriptionContext.Provider
      value={{
        tier,
        cycleResetDate,
        usage,
        limits,
        loading,
        refreshEntitlements,
      }}
    >
      {children}
    </SubscriptionContext.Provider>
  );
};
