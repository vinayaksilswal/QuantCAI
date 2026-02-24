import { Component, ErrorInfo, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    private handleReset = () => {
        this.setState({ hasError: false, error: null });
        window.location.reload();
    };

    private handleGoHome = () => {
        this.setState({ hasError: false, error: null });
        window.location.href = "/";
    };

    public render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex items-center justify-center bg-[#0a0f1d] p-6 text-white text-center">
                    <div className="max-w-md w-full space-y-8 p-10 bg-slate-900/60 border border-slate-800 backdrop-blur-md rounded-2xl shadow-2xl">
                        <div className="flex flex-col items-center">
                            <div className="p-4 rounded-full bg-red-500/10 text-red-500 mb-6">
                                <AlertTriangle className="h-12 w-12" />
                            </div>
                            <h1 className="text-3xl font-bold tracking-tight mb-2">Something went wrong</h1>
                            <p className="text-slate-400 mb-8">
                                The application encountered an unexpected error. We've been notified and are working on it.
                            </p>

                            <div className="flex flex-col sm:flex-row gap-4 w-full">
                                <Button
                                    onClick={this.handleReset}
                                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center gap-2"
                                >
                                    <RefreshCw className="h-4 w-4" />
                                    Try Again
                                </Button>
                                <Button
                                    variant="outline"
                                    onClick={this.handleGoHome}
                                    className="flex-1 border-slate-700 hover:bg-slate-800 text-white flex items-center justify-center gap-2"
                                >
                                    <Home className="h-4 w-4" />
                                    Go Home
                                </Button>
                            </div>

                            {process.env.NODE_ENV === 'development' && this.state.error && (
                                <div className="mt-8 p-4 bg-slate-950 rounded-lg text-left overflow-auto max-h-40 w-full">
                                    <p className="text-red-400 font-mono text-xs mb-2">Error Detail (Dev Only):</p>
                                    <pre className="text-slate-500 font-mono text-[10px] whitespace-pre-wrap">
                                        {this.state.error.toString()}
                                    </pre>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
