import { useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';

export function usePageTracking(pageKey: string) {
  const { user } = useAuth();

  useEffect(() => {
    // Page tracking - can be extended to send to backend API when endpoint is available
    // For now, just log to console or send analytics if needed
    const trackPage = async () => {
      try {
        // TODO: Implement backend endpoint for page tracking
        // await api.trackPageVisit(pageKey, user?.id);
        console.log(`Page tracked: ${pageKey}`, user ? `User: ${user.id}` : 'Anonymous');
      } catch {
        // ignore tracking errors
      }
    };
    trackPage();
  }, [pageKey, user]);
}

