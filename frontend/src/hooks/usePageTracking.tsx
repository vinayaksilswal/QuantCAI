import { useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api';

export function usePageTracking(pageKey: string) {
  const { user } = useAuth();

  useEffect(() => {
    const trackPage = async () => {
      if (!user) return;
      try {
        await api.trackProgress(pageKey);
        console.info(`Page tracked: ${pageKey}`);
      } catch (err) {
        console.warn(`Failed to track page ${pageKey}:`, err);
      }
    };
    trackPage();
  }, [pageKey, user]);
}

