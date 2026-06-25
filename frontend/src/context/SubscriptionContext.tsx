import { createContext, useContext, useEffect, useState, ReactNode, useCallback, useRef } from 'react';
import { fetchApi } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';

// In-memory cache for entitlements (5-minute TTL)
interface CacheEntry {
  data: any;
  timestamp: number;
}
const CACHE_TTL_MS = 5 * 60 * 1000;
let entitlementsCache: CacheEntry | null = null;

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

  const refreshEntitlements = useCallback(async (force = false) => {
    if (!user) {
      setTier('FREE');
      setCycleResetDate('');
      setUsage(defaultUsage);
      setLimits(defaultLimits);
      setLoading(false);
      entitlementsCache = null; // Clear cache on logout
      return;
    }

    // Check cache
    if (!force && entitlementsCache && Date.now() - entitlementsCache.timestamp < CACHE_TTL_MS) {
      const data = entitlementsCache.data;
      setTier(data.tier);
      setCycleResetDate(data.cycle_reset_date);
      setUsage(data.usage);
      setLimits(data.limits);
      setLoading(false);
      return;
    }

    let retries = 3;
    let data: any = null;

    while (retries > 0) {
      try {
        data = await fetchApi<{
          tier: 'FREE' | 'PRO' | 'ENTERPRISE';
          cycle_reset_date: string;
          usage: Usage;
          limits: Entitlements;
        }>('/api/v1/entitlements');
        break; // Success
      } catch (err) {
        retries -= 1;
        if (retries === 0) {
          console.error('Error fetching entitlements after 3 attempts:', err);
        } else {
          // Exponential backoff: 1s, 2s
          await new Promise(r => setTimeout(r, 1000 * Math.pow(2, 3 - retries - 1)));
        }
      }
    }

    if (data) {
      setTier(data.tier);
      setCycleResetDate(data.cycle_reset_date);
      setUsage(data.usage);
      setLimits(data.limits);
      // Update cache
      entitlementsCache = { data, timestamp: Date.now() };
    }
    
    setLoading(false);
  }, [user]);

  useEffect(() => {
    refreshEntitlements();
  }, [refreshEntitlements]);

  // Listen for subscription-updated events to force refresh entitlements dynamically
  useEffect(() => {
    const handleUpdate = () => {
      refreshEntitlements(true); // Force refresh bypassing cache
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
