import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import { ReactElement, lazy, Suspense } from "react";
import Index from "./pages/Index";

// Lazy load pages
const Learn = lazy(() => import("./pages/Learn"));
const QuantumComputing = lazy(() => import("./pages/QuantumComputing"));
const LearnQubits = lazy(() => import("./pages/LearnQubits"));
const LearnGates = lazy(() => import("./pages/LearnGates"));
const LearnPQC = lazy(() => import("./pages/LearnPQC"));
const QuantumStates = lazy(() => import("./pages/QuantumStates"));
const Tools = lazy(() => import("./pages/Tools"));
const CircuitBuilder = lazy(() => import("./pages/CircuitBuilder"));
const GetStarted = lazy(() => import("./pages/GetStarted"));
const Soon = lazy(() => import("./pages/Soon"));
const Community = lazy(() => import("./pages/Community"));
const Vision = lazy(() => import("./pages/Vision"));
const Admin = lazy(() => import("./pages/Admin"));
const Login = lazy(() => import("./pages/Login"));
const Profile = lazy(() => import("./pages/Profile"));
const AuthCallback = lazy(() => import("./pages/AuthCallback"));
// const Dashboard = lazy(() => import("./pages/Dashboard"));
const QuantumSimulator = lazy(() => import("./pages/QuantumSimulator"));
const NotFound = lazy(() => import("./pages/NotFound"));
const PqcScanner = lazy(() => import("./pages/PqcScanner"));
const Enterprise = lazy(() => import("./pages/Enterprise"));
import { AuthProvider } from "./context/AuthContext";
import { SubscriptionProvider } from "./context/SubscriptionContext";

import { useAuth } from "./hooks/useAuth";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { QuantumBackground } from "./components/QuantumBackground";
import { AIProvider } from "./context/AIContext";
import { AIAssistant } from "./components/AIAssistant";
import { TeachingOverlay } from "./components/TeachingOverlay";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { PaymentAutoTrigger } from "./components/PaymentAutoTrigger";
import { ScrollToTop } from "./components/ScrollToTop";

const queryClient = new QueryClient();


const RootRedirect = ({ children }: { children: ReactElement }) => {
  const { role } = useAuth();
  if (role === 'root') {
    return <Admin />; // show admin by default for root
  }
  return children;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <AuthProvider>
          <SubscriptionProvider>
            <ErrorBoundary>
              <BrowserRouter>
              <ScrollToTop />
              <AIProvider>
                {/* Global Animated Background - visible on all pages */}
                <QuantumBackground />
                <div className="relative z-10">
                  <Suspense fallback={
                    <div className="min-h-screen flex items-center justify-center bg-[#0a0f1d]">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
                    </div>
                  }>
                    <Routes>
                      <Route path="/" element={<RootRedirect><Index /></RootRedirect>} />
                      <Route path="/dashboard" element={<Navigate to="/profile" replace />} />
                      <Route path="/quantum-simulator" element={<ProtectedRoute roles={["root", "developer", "user", "learner", "enterprise_user"]}><QuantumSimulator /></ProtectedRoute>} />
                      <Route path="/learn" element={<Learn />} />
                      <Route path="/quantum-computing" element={<QuantumComputing />} />
                      <Route path="/learn/qubits" element={<LearnQubits />} />
                      <Route path="/learn/gates" element={<LearnGates />} />
                      <Route path="/learn/pqc" element={<LearnPQC />} />
                      <Route path="/quantum-states" element={<ProtectedRoute roles={["root", "developer", "user", "learner", "enterprise_user"]}><QuantumStates /></ProtectedRoute>} />
                      <Route path="/tools" element={<Tools />} />
                      <Route path="/circuit-builder" element={<ProtectedRoute roles={["root", "developer", "user", "learner", "enterprise_user"]}><CircuitBuilder /></ProtectedRoute>} />
                      <Route path="/get-started" element={<GetStarted />} />
                      <Route path="/soon" element={<Soon />} />
                      <Route path="/community" element={<Community />} />
                      <Route path="/vision" element={<Vision />} />
                      <Route path="/admin" element={<ProtectedRoute roles={["root"]}><Admin /></ProtectedRoute>} />
                      <Route path="/login" element={<Login />} />
                      <Route path="/signup" element={<Login />} />
                      <Route path="/register" element={<Login />} />
                      <Route path="/auth/callback" element={<AuthCallback />} />
                      <Route path="/profile" element={<ProtectedRoute roles={["root", "developer", "user", "learner", "enterprise_user"]}><Profile /></ProtectedRoute>} />
                      <Route path="/pqc-scanner" element={<ProtectedRoute roles={["root", "developer", "user", "learner", "enterprise_user"]}><PqcScanner /></ProtectedRoute>} />
                      <Route path="/enterprise/pqc-scanner" element={<ProtectedRoute roles={["root", "enterprise_user"]}><PqcScanner /></ProtectedRoute>} />
                      <Route path="/sandbox" element={<ProtectedRoute roles={["root", "developer", "user", "learner", "enterprise_user"]}><QuantumSimulator /></ProtectedRoute>} />
                      <Route path="/enterprise" element={<Enterprise />} />

                      <Route path="*" element={<Suspense fallback={null}><NotFound /></Suspense>} />
                    </Routes>
                  </Suspense>
                </div>
                <AIAssistant />
                <TeachingOverlay />
                <PaymentAutoTrigger />
              </AIProvider>
              </BrowserRouter>
            </ErrorBoundary>
          </SubscriptionProvider>
        </AuthProvider>

      </TooltipProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
