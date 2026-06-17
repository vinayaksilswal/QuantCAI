import React, { useEffect, useState, useRef } from 'react';
import { Loader2, CheckCircle2, AlertCircle, RefreshCw, X } from 'lucide-react';
import { API_BASE } from '@/lib/api';

type WakerStatus = 'checking' | 'sleeping' | 'waking' | 'online' | 'error';

export const BackendWaker: React.FC = () => {
  const [status, setStatus] = useState<WakerStatus>('checking');
  const [progress, setProgress] = useState(0);
  const [visible, setVisible] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const statusRef = useRef<WakerStatus>('checking');
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const wakeTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Keep ref in sync for interval callbacks
  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  const pingBackend = async (timeoutMs = 1800): Promise<boolean> => {
    const pingUrl = API_BASE ? `${API_BASE}/health` : '/health';
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(pingUrl, {
        signal: controller.signal,
        headers: { 'Cache-Control': 'no-cache' }
      });
      clearTimeout(timer);
      return response.ok;
    } catch (error) {
      clearTimeout(timer);
      return false;
    }
  };

  const startWakingProcess = () => {
    setStatus('waking');
    setVisible(true);
    setProgress(0);

    // Progress bar simulation (reaches 95% in ~50 seconds)
    const totalDuration = 50000; // 50s
    const stepTime = 100; // update every 100ms
    const increment = (95 / (totalDuration / stepTime));

    progressIntervalRef.current = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 95) {
          if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
          return 95;
        }
        return Math.min(95, prev + increment);
      });
    }, stepTime);

    // Keep polling every 4 seconds until awake
    pollIntervalRef.current = setInterval(async () => {
      const isOk = await pingBackend(3000);
      if (isOk && statusRef.current !== 'online') {
        handleSuccess();
      }
    }, 4000);

    // If it takes more than 90 seconds, transition to error state
    wakeTimeoutRef.current = setTimeout(() => {
      cleanupTimers();
      setStatus('error');
    }, 90000);
  };

  const handleSuccess = () => {
    cleanupTimers();
    setStatus('online');
    setProgress(100);

    // Auto-dismiss success message after 3 seconds
    setTimeout(() => {
      setVisible(false);
    }, 3500);
  };

  const cleanupTimers = () => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
    if (wakeTimeoutRef.current) clearTimeout(wakeTimeoutRef.current);
  };

  const handleRetry = async () => {
    setStatus('checking');
    setProgress(0);
    const isOk = await pingBackend(3000);
    if (isOk) {
      handleSuccess();
    } else {
      startWakingProcess();
    }
  };

  useEffect(() => {
    const initCheck = async () => {
      // Step 1: Check if backend is already online (short 1.5s timeout)
      const isOnlineImmediate = await pingBackend(1500);
      if (isOnlineImmediate) {
        setStatus('online');
        // Backend is already awake; keep visible=false to not annoy user
      } else {
        // Step 2: Backend is sleeping, start waking process and show toast
        setStatus('sleeping');
        startWakingProcess();
      }
    };

    initCheck();

    return () => {
      cleanupTimers();
    };
  }, []);

  if (!visible || dismissed) return null;

  return (
    <div className="fixed bottom-6 right-6 z-[9999] max-w-sm w-full bg-slate-950/90 border border-slate-800/80 backdrop-blur-md rounded-xl p-4 shadow-2xl transition-all duration-500 ease-out transform animate-fade-in">
      <button 
        onClick={() => setDismissed(true)}
        className="absolute top-2 right-2 text-slate-500 hover:text-slate-300 transition-colors"
        aria-label="Dismiss notification"
      >
        <X className="w-4 h-4" />
      </button>

      <div className="flex gap-3">
        {/* Icon container */}
        <div className="flex-shrink-0 mt-0.5">
          {status === 'waking' && (
            <div className="relative flex items-center justify-center">
              <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
              <div className="absolute inset-0 bg-blue-500/25 blur-sm rounded-full animate-ping" />
            </div>
          )}
          {status === 'online' && (
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          )}
          {status === 'error' && (
            <AlertCircle className="w-5 h-5 text-rose-400" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 pr-4">
          <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
            {status === 'waking' && 'Securing Quantum Sandbox...'}
            {status === 'online' && 'Sandbox Environment Ready'}
            {status === 'error' && 'Connection Timeout'}
          </h4>

          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            {status === 'waking' && 'Preparing your secure quantum computing workspace. Establishing encrypted handshake...'}
            {status === 'online' && 'Secure quantum link established. All simulation protocols are operational.'}
            {status === 'error' && 'The secure workspace took too long to initialize. Please try reloading or clicking retry.'}
          </p>

          {/* Progress bar or Retry Action */}
          {status === 'waking' && (
            <div className="mt-3">
              <div className="flex justify-between items-center text-[10px] text-slate-500 font-mono mb-1">
                <span>INITIALIZATION PROGRESS</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800/40">
                <div 
                  className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-300 ease-out" 
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {status === 'online' && (
            <div className="mt-3">
              <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800/40">
                <div className="h-full bg-emerald-500 rounded-full w-full transition-all duration-500 ease-out" />
              </div>
            </div>
          )}

          {status === 'error' && (
            <button
              onClick={handleRetry}
              className="mt-3 flex items-center gap-1.5 px-3 py-1.5 bg-rose-950/40 hover:bg-rose-900/40 border border-rose-800/50 hover:border-rose-700/60 rounded-lg text-xs font-medium text-rose-300 transition-all duration-200"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Retry Connection
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
