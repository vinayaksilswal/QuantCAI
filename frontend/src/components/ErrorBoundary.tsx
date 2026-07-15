import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ShieldAlert, RefreshCw, Home } from 'lucide-react';
import { Button } from './ui/button';
import { Link } from 'react-router-dom';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
          <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 via-transparent to-orange-500/5 pointer-events-none" />
          <div className="max-w-md w-full bg-slate-900/60 backdrop-blur-xl border border-red-500/20 rounded-2xl p-8 text-center shadow-2xl relative z-10">
            <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-6 border border-red-500/20">
              <ShieldAlert className="h-8 w-8 text-red-400" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-3">System Anomaly Detected</h1>
            <p className="text-slate-400 text-sm mb-6 leading-relaxed">
              We encountered an unexpected error while processing your request. Our quantum sensors have logged the anomaly.
            </p>
            {this.state.error && (
              <div className="bg-black/40 rounded-lg p-3 mb-6 text-left overflow-hidden border border-white/5">
                <p className="text-red-400 font-mono text-[10px] sm:text-xs truncate">
                  {this.state.error.message}
                </p>
              </div>
            )}
            <div className="flex flex-col gap-3">
              <Button 
                onClick={() => window.location.reload()}
                className="w-full bg-gradient-to-r from-red-500/80 to-orange-500/80 hover:from-red-500 hover:to-orange-500 text-white border-none shadow-lg shadow-red-500/20"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Reinitialize Session
              </Button>
              <Link to="/">
                <Button variant="outline" className="w-full border-slate-700 hover:bg-slate-800 text-slate-300">
                  <Home className="mr-2 h-4 w-4" />
                  Return to Dashboard
                </Button>
              </Link>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
