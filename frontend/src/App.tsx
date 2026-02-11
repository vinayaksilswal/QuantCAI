import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import { ReactElement, lazy, Suspense } from "react";
import Index from "./pages/Index";

// Lazy load pages
const Learn = lazy(() => import("./pages/Learn"));
const QuantumComputing = lazy(() => import("./pages/QuantumComputing"));
const QuantumStates = lazy(() => import("./pages/QuantumStates"));
const Tools = lazy(() => import("./pages/Tools"));
const CircuitBuilder = lazy(() => import("./pages/CircuitBuilder"));
const GetStarted = lazy(() => import("./pages/GetStarted"));
const Soon = lazy(() => import("./pages/Soon"));
const Community = lazy(() => import("./pages/Community"));
const Vision = lazy(() => import("./pages/Vision"));
const Admin = lazy(() => import("./pages/Admin"));
const Developer = lazy(() => import("./pages/Developer"));
const Login = lazy(() => import("./pages/Login"));
const Profile = lazy(() => import("./pages/Profile"));
const NotFound = lazy(() => import("./pages/NotFound"));

import { AuthProvider } from "./context/AuthContext";
import { useAuth } from "./hooks/useAuth";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { QuantumBackground } from "./components/QuantumBackground";
import { AIProvider } from "./context/AIContext";
import { AIAssistant } from "./components/AIAssistant";
import { TeachingOverlay } from "./components/TeachingOverlay";

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
          <BrowserRouter>
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
                    <Route path="/learn" element={<Learn />} />
                    <Route path="/quantum-computing" element={<QuantumComputing />} />
                    <Route path="/quantum-states" element={<ProtectedRoute roles={["root", "developer", "user"]}><QuantumStates /></ProtectedRoute>} />
                    <Route path="/tools" element={<Tools />} />
                    <Route path="/circuit-builder" element={<ProtectedRoute roles={["root", "developer", "user"]}><CircuitBuilder /></ProtectedRoute>} />
                    <Route path="/get-started" element={<GetStarted />} />
                    <Route path="/soon" element={<Soon />} />
                    <Route path="/community" element={<Community />} />
                    <Route path="/vision" element={<Vision />} />
                    <Route path="/admin" element={<ProtectedRoute roles={["root"]}><Admin /></ProtectedRoute>} />
                    <Route path="/developer" element={<ProtectedRoute roles={["root", "developer"]}><Developer /></ProtectedRoute>} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/profile" element={<ProtectedRoute roles={["root", "developer", "user"]}><Profile /></ProtectedRoute>} />
                    <Route path="*" element={<Suspense fallback={null}><NotFound /></Suspense>} />
                  </Routes>
                </Suspense>
              </div>
              <AIAssistant />
              <TeachingOverlay />
            </AIProvider>
          </BrowserRouter>
        </AuthProvider>
      </TooltipProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
