import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import { ReactElement } from "react";
import Index from "./pages/Index";
import Learn from "./pages/Learn";
import QuantumComputing from "./pages/QuantumComputing";
import QuantumStates from "./pages/QuantumStates";
import Tools from "./pages/Tools";
import CircuitBuilder from "./pages/CircuitBuilder";
import GetStarted from "./pages/GetStarted";
import Soon from "./pages/Soon";
import Community from "./pages/Community";
import Vision from "./pages/Vision";
import NotFound from "./pages/NotFound";
import Admin from "./pages/Admin";
import Developer from "./pages/Developer";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
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
                  <Route path="*" element={<NotFound />} />
                </Routes>
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
