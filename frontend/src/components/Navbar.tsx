import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { Menu, X, ChevronDown, BookOpen, Atom, Zap, Target, User, LogOut, Home, Users, Eye, Rocket } from 'lucide-react';
import { LogoProcessor } from './LogoProcessor';
import { useAuth } from '@/hooks/useAuth';

// Learning paths configuration
const learningPaths = [
  { path: '/learn', label: 'Learning Hub', icon: BookOpen, description: 'Start your journey' },
  { path: '/quantum-computing', label: 'Quantum Basics', icon: Atom, description: 'Fundamentals' },
];

export const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isLearnOpen, setIsLearnOpen] = useState(false);
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
    <nav className="fixed top-0 w-full z-50 bg-slate-900/95 backdrop-blur-xl border-b border-blue-500/30 shadow-lg shadow-blue-500/10">
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
          <div className="hidden lg:flex items-center space-x-1">
            <Link
              to="/"
              className={`px-3 py-1 rounded-lg transition-all duration-200 flex items-center gap-2 ${isActive('/')
                ? 'bg-blue-600/30 text-white font-medium shadow-lg shadow-blue-500/20'
                : 'text-blue-200 hover:text-white hover:bg-blue-600/20'
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
                className={`px-3 py-1 rounded-lg transition-all duration-200 flex items-center gap-2 relative ${isActive('/learn') || isActive('/quantum-computing') || isActive('/quantum-states')
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium shadow-lg shadow-purple-500/30'
                  : 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-100 hover:from-blue-500/40 hover:to-purple-500/40 hover:text-white border border-blue-400/30'
                  }`}
              >
                <BookOpen className="h-4 w-4" />
                <span>Learn</span>
                <ChevronDown className="h-3 w-3 ml-1" />
              </button>

              {isLearnOpen && (
                <div className="absolute top-full left-0 mt-2 w-80 bg-slate-800/98 backdrop-blur-xl rounded-xl border border-blue-500/30 py-3 shadow-2xl shadow-blue-500/20">
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
                            ? 'bg-blue-600/30 text-white border border-blue-500/50'
                            : 'text-blue-100 hover:text-white hover:bg-blue-600/20'
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
                ? 'bg-blue-600/30 text-white font-medium shadow-lg shadow-blue-500/20'
                : 'text-blue-200 hover:text-white hover:bg-blue-600/20'
                }`}
            >
              <Zap className="h-4 w-4" />
              Tools
            </Link>

            <Link
              to="/community"
              className={`px-3 py-1 rounded-lg transition-all duration-200 flex items-center gap-2 ${isActive('/community')
                ? 'bg-blue-600/30 text-white font-medium'
                : 'text-blue-200 hover:text-white hover:bg-blue-600/20'
                }`}
            >
              <Users className="h-4 w-4" />
              Community
            </Link>

            <Link
              to="/soon"
              className={`px-3 py-1 rounded-lg transition-all duration-200 flex items-center gap-2 ${isActive('/soon')
                ? 'bg-blue-600/30 text-white font-medium'
                : 'text-blue-200 hover:text-white hover:bg-blue-600/20'
                }`}
            >
              <Rocket className="h-4 w-4" />
              Soon
            </Link>

            <Link
              to="/vision"
              className={`px-3 py-1 rounded-lg transition-all duration-200 flex items-center gap-2 ${isActive('/vision')
                ? 'bg-blue-600/30 text-white font-medium'
                : 'text-blue-200 hover:text-white hover:bg-blue-600/20'
                }`}
            >
              <Eye className="h-4 w-4" />
              Vision
            </Link>

            {role === 'root' && (
              <Link
                to="/admin"
                className="px-3 py-1 rounded-lg transition-all duration-200 text-purple-200 hover:text-white hover:bg-purple-600/20 flex items-center gap-2"
              >
                <Target className="h-4 w-4" />
                Admin
              </Link>
            )}
          </div>

          {/* Desktop Actions */}
          <div className="hidden lg:flex items-center space-x-3">
            {!user ? (
              <>
                <Link to="/login">
                  <Button variant="ghost" className="text-blue-200 hover:text-white hover:bg-blue-600/20">
                    Log In
                  </Button>
                </Link>
                <Link to="/get-started">
                  <Button className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-lg shadow-blue-500/25 flex items-center gap-2">
                    <Rocket className="h-4 w-4" />
                    Get Started
                  </Button>
                </Link>
              </>
            ) : (
              <>
                <Link to="/profile">
                  <Button variant="ghost" className="text-blue-200 hover:text-white hover:bg-blue-600/20 flex items-center gap-2">
                    <User className="h-4 w-4" />
                    Profile
                  </Button>
                </Link>
                <Button onClick={signOut} variant="ghost" className="text-blue-200 hover:text-white hover:bg-blue-600/20 flex items-center gap-2">
                  <LogOut className="h-4 w-4" />
                  Log Out
                </Button>
              </>
            )}
          </div>

          {/* Mobile Menu Toggle */}
          <button
            className="lg:hidden text-white p-2 hover:bg-blue-600/20 rounded-lg transition-colors"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="lg:hidden bg-slate-800/98 backdrop-blur-xl rounded-xl mb-4 p-4 border border-blue-500/30 shadow-xl">
            <div className="flex flex-col space-y-2">
              <Link
                to="/"
                className={`px-4 py-3 rounded-lg transition-all flex items-center gap-3 ${isActive('/')
                  ? 'bg-blue-600/30 text-white font-medium'
                  : 'text-blue-200 hover:text-white hover:bg-blue-600/20'
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
                  className={`w-full px-4 py-3 rounded-lg transition-all flex items-center justify-between ${isActive('/learn') || isActive('/quantum-computing') || isActive('/quantum-states')
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium shadow-lg'
                    : 'bg-gradient-to-r from-blue-500/30 to-purple-500/30 text-blue-100 border border-blue-400/30'
                    }`}
                >
                  <div className="flex items-center gap-3">
                    <BookOpen className="h-5 w-5" />
                    <span className="font-semibold">Learn</span>
                  </div>
                  <ChevronDown className={`h-4 w-4 transition-transform ${isLearnOpen ? 'rotate-180' : ''}`} />
                </button>

                {isLearnOpen && (
                  <div className="ml-4 space-y-1 border-l-2 border-blue-500/30 pl-4">
                    {learningPaths.map((item) => {
                      const Icon = item.icon;
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          className={`block px-3 py-1 rounded-lg transition-all ${isActive(item.path)
                            ? 'bg-blue-600/30 text-white'
                            : 'text-blue-200 hover:text-white hover:bg-blue-600/20'
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
                to="/community"
                className={`px-4 py-3 rounded-lg transition-all flex items-center gap-3 ${isActive('/community')
                  ? 'bg-blue-600/30 text-white font-medium'
                  : 'text-blue-200 hover:text-white hover:bg-blue-600/20'
                  }`}
                onClick={() => setIsMenuOpen(false)}
              >
                <Users className="h-5 w-5" />
                Community
              </Link>

              <Link
                to="/soon"
                className={`px-4 py-3 rounded-lg transition-all flex items-center gap-3 ${isActive('/soon')
                  ? 'bg-blue-600/30 text-white font-medium'
                  : 'text-blue-200 hover:text-white hover:bg-blue-600/20'
                  }`}
                onClick={() => setIsMenuOpen(false)}
              >
                <Rocket className="h-5 w-5" />
                Soon
              </Link>

              <Link
                to="/vision"
                className={`px-4 py-3 rounded-lg transition-all flex items-center gap-3 ${isActive('/vision')
                  ? 'bg-blue-600/30 text-white font-medium'
                  : 'text-blue-200 hover:text-white hover:bg-blue-600/20'
                  }`}
                onClick={() => setIsMenuOpen(false)}
              >
                <Eye className="h-5 w-5" />
                Vision
              </Link>

              {role === 'root' && (
                <Link
                  to="/admin"
                  className="px-4 py-3 rounded-lg transition-all text-purple-200 hover:text-white hover:bg-purple-600/20 flex items-center gap-3"
                  onClick={() => setIsMenuOpen(false)}
                >
                  <Target className="h-5 w-5" />
                  Admin
                </Link>
              )}

              <div className="flex flex-col space-y-2 pt-4 border-t border-blue-700/50">
                {!user ? (
                  <>
                    <Link to="/login" onClick={() => setIsMenuOpen(false)}>
                      <Button variant="ghost" className="w-full text-blue-200 hover:text-white justify-start">
                        <User className="h-5 w-5 mr-2" />
                        Log In
                      </Button>
                    </Link>
                    <Link to="/get-started" onClick={() => setIsMenuOpen(false)}>
                      <Button className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white flex items-center justify-center gap-2">
                        <Rocket className="h-4 w-4" />
                        Get Started
                      </Button>
                    </Link>
                  </>
                ) : (
                  <>
                    <Link to="/profile" onClick={() => setIsMenuOpen(false)}>
                      <Button variant="ghost" className="w-full text-blue-200 hover:text-white justify-start">
                        <User className="h-5 w-5 mr-2" />
                        Profile
                      </Button>
                    </Link>
                    <Button
                      onClick={() => { signOut(); setIsMenuOpen(false); }}
                      variant="ghost"
                      className="w-full text-blue-200 hover:text-white justify-start"
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
