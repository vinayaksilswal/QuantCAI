import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { Menu, X, ChevronDown, BookOpen, Atom, Zap, Target, User, LogOut, Home, Users, Eye, Rocket, Shield, Bell, CreditCard } from 'lucide-react';
import { LogoProcessor } from './LogoProcessor';
import { useAuth } from '@/hooks/useAuth';

// Learning paths configuration
const learningPaths = [
  { path: '/learn', label: 'Quantum Cohorts', icon: Rocket, description: 'Live Cohort Programs' },
  { path: '/quantum-computing', label: 'Quantum Basics', icon: Atom, description: 'Fundamentals' },
  { path: '/learn/qubits', label: 'Module 1: Qubits', icon: Target, description: 'Pro Curriculum' },
  { path: '/learn/gates', label: 'Module 2: Gates', icon: Zap, description: 'Pro Curriculum' },
  { path: '/learn/pqc', label: 'Module 3: PQC', icon: Shield, description: 'Pro Curriculum' },
];

export const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isLearnOpen, setIsLearnOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut, role } = useAuth();

  const isActive = (path: string) => location.pathname === path;

  const handleLearnClick = () => {
    navigate('/learn');
    setIsLearnOpen(false);
    setIsMenuOpen(false);
  };

  return (
    <nav className="fixed top-0 w-full z-50 bg-qc-bg-raised backdrop-blur-xl border-b border-qc-border shadow-lg shadow-blue-500/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          {/* Logo - Bigger and more visible */}
          <Link to="/" className="flex items-center group p-0">
            <LogoProcessor
              originalSrc="/lovable-uploads/56a0d2c9-73da-4624-bfb1-2bb520c4a4e3.png"
              alt="QuantCAI Logo"
              className="h-8 sm:h-10 transition-transform duration-300 group-hover:scale-110"
              style={{
                filter: 'drop-shadow(0 0 20px rgba(59, 130, 246, 0.8)) brightness(1.3) contrast(1.4) saturate(1.3)',
                mixBlendMode: 'screen'
              }}
            />
          </Link>

          {/* Desktop Navigation - Order: Home, Learn, Community, Soon, Vision */}
          <div className="hidden lg:flex items-center space-x-1 text-sm">
            <Link
              to="/"
              className={`px-3 py-1 rounded-lg transition-all duration-200 flex items-center gap-2 ${isActive('/')
                ? 'bg-qc-accent-dim text-qc-text font-medium shadow-lg shadow-blue-500/20'
                : 'text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover'
                }`}
            >
              <Home className="h-4 w-4" />
              Home
            </Link>

            {/* Prominent Learn Section */}
            <div
              className="relative"
              onMouseEnter={() => setIsLearnOpen(true)}
              onMouseLeave={() => setIsLearnOpen(false)}
            >
              <button
                onClick={handleLearnClick}
                className={`px-3 py-1 rounded-lg transition-all duration-200 flex items-center gap-2 relative ${isActive('/learn') || isActive('/quantum-computing') || isActive('/quantum-states') || location.pathname.startsWith('/learn/')
                  ? 'bg-qc-accent text-qc-text font-medium shadow-lg shadow-purple-500/30'
                  : 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-qc-muted hover:from-blue-500/40 hover:to-purple-500/40 hover:text-qc-text border border-qc-border'
                  }`}
              >
                <BookOpen className="h-4 w-4" />
                <span>Learn</span>
                <ChevronDown className="h-3 w-3 ml-1" />
              </button>

              {isLearnOpen && (
                <div className="absolute top-full left-0 mt-2 w-80 bg-qc-bg-raised backdrop-blur-xl rounded-xl border border-qc-border py-3 shadow-2xl shadow-blue-500/20">
                  {/* Learning Paths */}
                  <div className="space-y-1">
                    {learningPaths.map((item) => {
                      const Icon = item.icon;
                      const isPathActive = isActive(item.path);
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          className={`block px-4 py-3 mx-2 rounded-lg transition-all duration-200 ${isPathActive
                            ? 'bg-qc-accent-dim text-qc-text border border-blue-500/50'
                            : 'text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover'
                            }`}
                        >
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${isPathActive ? 'bg-blue-500/30' : 'bg-blue-500/10'
                              }`}>
                              <Icon className="h-4 w-4" />
                            </div>
                            <div className="flex-1">
                              <div className="font-medium">{item.label}</div>
                              <div className="text-xs text-gray-400">{item.description}</div>
                            </div>
                            {isPathActive && (
                              <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse"></div>
                            )}
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            <Link
              to="/tools"
              className={`px-3 py-1 rounded-lg transition-all duration-200 flex items-center gap-2 ${isActive('/tools')
                ? 'bg-qc-accent-dim text-qc-text font-medium shadow-lg shadow-blue-500/20'
                : 'text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover'
                }`}
            >
              <Zap className="h-4 w-4" />
              Tools
            </Link>

            {(role === 'enterprise_user' || role === 'root') && (
              <Link
                to="/enterprise/pqc-scanner"
                className={`px-3 py-1 rounded-lg transition-all duration-200 flex items-center gap-2 relative ${isActive('/enterprise/pqc-scanner')
                  ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-qc-text font-medium shadow-lg shadow-teal-500/30'
                  : 'text-emerald-400 hover:text-qc-text hover:bg-emerald-600/20'
                  }`}
              >
                <Shield className="h-4 w-4" />
                PQC Compliance
                <span className="absolute -top-1 -right-2 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
              </Link>
            )}

            <Link
              to="/community"
              className={`px-3 py-1 rounded-lg transition-all duration-200 flex items-center gap-2 ${isActive('/community')
                ? 'bg-qc-accent-dim text-qc-text font-medium'
                : 'text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover'
                }`}
            >
              <Users className="h-4 w-4" />
              Community
            </Link>

            <Link
              to="/soon"
              className={`px-3 py-1 rounded-lg transition-all duration-200 flex items-center gap-2 ${isActive('/soon')
                ? 'bg-qc-accent-dim text-qc-text font-medium'
                : 'text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover'
                }`}
            >
              <Rocket className="h-4 w-4" />
              Upcoming Features
            </Link>

            <Link
              to="/vision"
              className={`px-3 py-1 rounded-lg transition-all duration-200 flex items-center gap-2 ${isActive('/vision')
                ? 'bg-qc-accent-dim text-qc-text font-medium'
                : 'text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover'
                }`}
            >
              <Eye className="h-4 w-4" />
              Vision
            </Link>

            {role === 'root' && (
              <Link
                to="/admin"
                className="px-3 py-1 rounded-lg transition-all duration-200 text-purple-200 hover:text-qc-text hover:bg-purple-600/20 flex items-center gap-2"
              >
                <Target className="h-4 w-4" />
                Admin
              </Link>
            )}
          </div>

          {/* Desktop Actions */}
          <div className="hidden lg:flex items-center space-x-3 text-sm">
            {!user ? (
              <>
                <a href="/#pricing" className="hidden xl:flex items-center gap-2 px-3 py-1 text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover rounded-lg transition-all">
                  <CreditCard className="h-4 w-4" />
                  Pricing
                </a>
                <Link to="/login">
                  <Button variant="ghost" className="text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover">
                    Log In
                  </Button>
                </Link>
                <Link to="/get-started">
                  <Button className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-qc-text shadow-lg shadow-blue-500/25 flex items-center gap-2">
                    <Rocket className="h-4 w-4" />
                    Get Started
                  </Button>
                </Link>
              </>
            ) : (
              <>
                <div className="relative">
                  <button 
                    onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
                    className="p-2 text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover rounded-full transition-colors relative"
                  >
                    <Bell className="h-5 w-5" />
                    <span className="absolute top-1 right-1 flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                    </span>
                  </button>
                  
                  {isNotificationsOpen && (
                    <div className="absolute right-0 mt-2 w-80 bg-[#0f172a] border border-qc-border rounded-xl shadow-2xl py-2 z-50">
                      <div className="px-4 py-2 border-b border-qc-border flex justify-between items-center">
                        <h3 className="font-syne font-bold text-qc-text">Notifications</h3>
                        <span className="bg-red-500 text-qc-text text-[10px] font-bold px-2 py-0.5 rounded-full">3 New</span>
                      </div>
                      <div className="max-h-[300px] overflow-y-auto">
                        <div className="px-4 py-3 hover:bg-blue-900/20 transition-colors cursor-pointer border-b border-blue-500/10">
                          <div className="flex items-start gap-3">
                            <div className="bg-emerald-500/20 p-2 rounded-lg mt-0.5">
                              <Zap className="h-4 w-4 text-emerald-400" />
                            </div>
                            <div>
                              <p className="text-sm font-medium text-qc-text mb-1 leading-tight">New Feature: PQC Scanner</p>
                              <p className="text-xs text-slate-400 leading-snug">Scan your repositories for Post-Quantum Cryptography vulnerabilities today!</p>
                              <p className="text-[10px] text-slate-500 mt-1">2 hours ago</p>
                            </div>
                          </div>
                        </div>
                        <div className="px-4 py-3 hover:bg-blue-900/20 transition-colors cursor-pointer border-b border-blue-500/10">
                          <div className="flex items-start gap-3">
                            <div className="bg-purple-500/20 p-2 rounded-lg mt-0.5">
                              <Rocket className="h-4 w-4 text-purple-400" />
                            </div>
                            <div>
                              <p className="text-sm font-medium text-qc-text mb-1 leading-tight">Summer Promotion 🌟</p>
                              <p className="text-xs text-slate-400 leading-snug">Upgrade to Enterprise plan and get 30% off your first 3 months.</p>
                              <p className="text-[10px] text-slate-500 mt-1">1 day ago</p>
                            </div>
                          </div>
                        </div>
                        <div className="px-4 py-3 hover:bg-blue-900/20 transition-colors cursor-pointer">
                          <div className="flex items-start gap-3">
                            <div className="bg-blue-500/20 p-2 rounded-lg mt-0.5">
                              <Atom className="h-4 w-4 text-qc-accent" />
                            </div>
                            <div>
                              <p className="text-sm font-medium text-qc-text mb-1 leading-tight">Quantum Simulator v2.0</p>
                              <p className="text-xs text-slate-400 leading-snug">Experience faster rendering and more precise entanglement visualizations.</p>
                              <p className="text-[10px] text-slate-500 mt-1">3 days ago</p>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="px-4 py-2 border-t border-qc-border text-center">
                        <button className="text-xs text-qc-accent hover:text-qc-muted font-medium transition-colors">
                          Mark all as read
                        </button>
                      </div>
                    </div>
                  )}
                </div>
                <Link to="/profile">
                  <Button variant="ghost" className="text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover flex items-center gap-2">
                    <User className="h-4 w-4" />
                    Profile
                  </Button>
                </Link>

                <Button onClick={signOut} variant="ghost" className="text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover flex items-center gap-2">
                  <LogOut className="h-4 w-4" />
                  Log Out
                </Button>
              </>
            )}
          </div>

          {/* Mobile Menu Toggle */}
          <button
            className="lg:hidden text-qc-text p-2 hover:bg-qc-surface-hover rounded-lg transition-colors"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="lg:hidden bg-qc-bg-raised backdrop-blur-xl rounded-xl mb-4 p-4 border border-qc-border shadow-xl">
            <div className="flex flex-col space-y-2">
              <Link
                to="/"
                className={`px-4 py-3 rounded-lg transition-all flex items-center gap-3 ${isActive('/')
                  ? 'bg-qc-accent-dim text-qc-text font-medium'
                  : 'text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover'
                  }`}
                onClick={() => setIsMenuOpen(false)}
              >
                <Home className="h-5 w-5" />
                Home
              </Link>

              {/* Mobile Learn Section - Prominent */}
              <div className="space-y-2">
                <button
                  onClick={() => setIsLearnOpen(!isLearnOpen)}
                  className={`w-full px-4 py-3 rounded-lg transition-all flex items-center justify-between ${isActive('/learn') || isActive('/quantum-computing') || isActive('/quantum-states') || location.pathname.startsWith('/learn/')
                    ? 'bg-qc-accent text-qc-text font-medium shadow-lg'
                    : 'bg-qc-surface-hover text-qc-muted border border-qc-border'
                    }`}
                >
                  <div className="flex items-center gap-3">
                    <BookOpen className="h-5 w-5" />
                    <span className="font-semibold">Learn</span>
                  </div>
                  <ChevronDown className={`h-4 w-4 transition-transform ${isLearnOpen ? 'rotate-180' : ''}`} />
                </button>

                {isLearnOpen && (
                  <div className="ml-4 space-y-1 border-l-2 border-qc-border pl-4">
                    {learningPaths.map((item) => {
                      const Icon = item.icon;
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          className={`block px-3 py-1 rounded-lg transition-all ${isActive(item.path)
                            ? 'bg-qc-accent-dim text-qc-text'
                            : 'text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover'
                            }`}
                          onClick={() => { setIsMenuOpen(false); setIsLearnOpen(false); }}
                        >
                          <div className="flex items-center gap-2">
                            <Icon className="h-4 w-4" />
                            <span>{item.label}</span>
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>

              <Link
                to="/tools"
                className={`px-4 py-3 rounded-lg transition-all flex items-center gap-3 ${isActive('/tools')
                  ? 'bg-qc-accent-dim text-qc-text font-medium shadow-lg shadow-blue-500/20'
                  : 'text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover'
                  }`}
                onClick={() => setIsMenuOpen(false)}
              >
                <Zap className="h-5 w-5" />
                Tools
              </Link>

              {(role === 'enterprise_user' || role === 'root') && (
                <Link
                  to="/enterprise/pqc-scanner"
                  className={`px-4 py-3 rounded-lg transition-all flex items-center gap-3 relative ${isActive('/enterprise/pqc-scanner')
                    ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-qc-text font-medium shadow-lg shadow-emerald-500/20 border border-emerald-500/30'
                    : 'text-emerald-400 hover:text-qc-text hover:bg-emerald-600/20'
                    }`}
                  onClick={() => setIsMenuOpen(false)}
                >
                  <Shield className="h-5 w-5" />
                  <span>PQC Compliance</span>
                  <span className="ml-auto bg-emerald-500 text-qc-text text-[10px] font-bold px-2 py-0.5 rounded-full">NEW</span>
                </Link>
              )}

              <Link
                to="/community"
                className={`px-4 py-3 rounded-lg transition-all flex items-center gap-3 ${isActive('/community')
                  ? 'bg-qc-accent-dim text-qc-text font-medium'
                  : 'text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover'
                  }`}
                onClick={() => setIsMenuOpen(false)}
              >
                <Users className="h-5 w-5" />
                Community
              </Link>

              <Link
                to="/soon"
                className={`px-4 py-3 rounded-lg transition-all flex items-center gap-3 ${isActive('/soon')
                  ? 'bg-qc-accent-dim text-qc-text font-medium'
                  : 'text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover'
                  }`}
                onClick={() => setIsMenuOpen(false)}
              >
                <Rocket className="h-5 w-5" />
                Upcoming Features
              </Link>

              <Link
                to="/vision"
                className={`px-4 py-3 rounded-lg transition-all flex items-center gap-3 ${isActive('/vision')
                  ? 'bg-qc-accent-dim text-qc-text font-medium'
                  : 'text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover'
                  }`}
                onClick={() => setIsMenuOpen(false)}
              >
                <Eye className="h-5 w-5" />
                Vision
              </Link>

              {role === 'root' && (
                <Link
                  to="/admin"
                  className="px-4 py-3 rounded-lg transition-all text-purple-200 hover:text-qc-text hover:bg-purple-600/20 flex items-center gap-3"
                  onClick={() => setIsMenuOpen(false)}
                >
                  <Target className="h-5 w-5" />
                  Admin
                </Link>
              )}

              <div className="flex flex-col space-y-2 pt-4 border-t border-blue-700/50">
                {!user ? (
                  <>
                    <a href="/#pricing" onClick={() => setIsMenuOpen(false)} className="px-4 py-3 text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover rounded-lg flex items-center gap-3">
                      <CreditCard className="h-5 w-5" />
                      Pricing
                    </a>
                    <Link to="/login" onClick={() => setIsMenuOpen(false)}>
                      <Button variant="ghost" className="w-full text-qc-muted hover:text-qc-text justify-start">
                        <User className="h-5 w-5 mr-2" />
                        Log In
                      </Button>
                    </Link>
                    <Link to="/get-started" onClick={() => setIsMenuOpen(false)}>
                      <Button className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-qc-text flex items-center justify-center gap-2">
                        <Rocket className="h-4 w-4" />
                        Get Started
                      </Button>
                    </Link>
                  </>
                ) : (
                  <>
                    <Link to="/profile" onClick={() => setIsMenuOpen(false)}>
                      <Button variant="ghost" className="w-full text-qc-muted hover:text-qc-text justify-start">
                        <User className="h-5 w-5 mr-2" />
                        Profile
                      </Button>
                    </Link>

                    <Button
                      onClick={() => { signOut(); setIsMenuOpen(false); }}
                      variant="ghost"
                      className="w-full text-qc-muted hover:text-qc-text justify-start"
                    >
                      <LogOut className="h-5 w-5 mr-2" />
                      Log Out
                    </Button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};
