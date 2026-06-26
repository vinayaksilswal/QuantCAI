import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { api, PageProgress } from '@/lib/api';
import { BookOpen, Bell, Shield, User as UserIcon, Calendar, AlertCircle, LayoutDashboard, Key, CreditCard, Settings as SettingsIcon, Terminal, Zap, ArrowRight } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useNavigate, useLocation } from 'react-router-dom';

import { OverviewTab } from '@/components/dashboard/OverviewTab';
import { DeveloperConsoleTab } from '@/components/dashboard/DeveloperConsoleTab';
import { ApiDocsTab } from '@/components/dashboard/ApiDocsTab';
import { BillingTab } from '@/components/dashboard/BillingTab';
import { SettingsTab } from '@/components/dashboard/SettingsTab';
import { UpgradeModal } from '@/components/UpgradeModal';

const Profile = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, role, session, subscriptionPlan } = useAuth();
  const [progress, setProgress] = useState<PageProgress[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loadingNotifications, setLoadingNotifications] = useState(false);
  const [activeSection, setActiveSection] = useState('account');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (location.state && (location.state as any).tab) {
      setActiveSection((location.state as any).tab);
    }
  }, [location.state]);

  useEffect(() => {
    const load = async () => {
      if (!user) return;
      try {
        const data = await api.getProgress();
        setProgress(Array.isArray(data) ? data : []);
      } catch (err: any) {
        console.error('Error loading progress:', err);
      }
    };
    load();
  }, [user]);

  useEffect(() => {
    const loadNotifications = async () => {
      if (role !== 'root' && role !== 'admin') return;
      try {
        setLoadingNotifications(true);
        const data = await api.listNotifications();
        setNotifications(Array.isArray(data) ? data : []);
      } catch (err: any) {
        console.error('Error loading notifications:', err);
        setError('Failed to load administrative notifications.');
      } finally {
        setLoadingNotifications(false);
      }
    };
    loadNotifications();
  }, [role]);

  const getInitials = (name: string) => {
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <div className="min-h-screen relative bg-transparent text-white">
      <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 via-transparent to-purple-500/5 pointer-events-none" />
      <UpgradeModal />
      <Navbar />

      <div className="pt-32 pb-20 px-4 md:px-8 max-w-7xl mx-auto relative z-10">
        {error && (
          <Alert variant="destructive" className="mb-6 bg-red-900/20 border-red-900/50 text-red-200">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="flex flex-col lg:flex-row gap-8 items-start">
          {/* Vertical Profile Navigation Sidebar */}
          <aside className="w-full lg:w-64 shrink-0 flex flex-col gap-1.5 p-4 rounded-2xl bg-slate-900/40 border border-slate-800/80 backdrop-blur-xl shadow-2xl">
            <div className="px-3 py-1.5 mb-2 border-b border-slate-800/60 pb-3">
              <p className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase">CONSOLE CONTROL</p>
              <div className="flex items-center gap-2 mt-2">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-xs text-slate-400 font-medium">Session Active</span>
              </div>
            </div>
            
            {[
              { id: 'account', label: 'Account Profile', icon: UserIcon },
              { id: 'overview', label: 'Workspace Overview', icon: LayoutDashboard },
              { id: 'developer', label: 'Developer Console', icon: Terminal },
              { id: 'apidocs', label: 'API Reference', icon: BookOpen },
              { id: 'billing', label: 'Billing & Plans', icon: CreditCard },
              { id: 'settings', label: 'Settings', icon: SettingsIcon },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeSection === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => tab.action ? tab.action() : setActiveSection(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-mono tracking-tight font-semibold transition-all duration-300 ${
                    isActive 
                      ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 border-l-4 border-blue-500 text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.15)] bg-slate-850/60' 
                      : 'text-slate-400 hover:bg-slate-800/40 hover:text-white'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </aside>

          {/* Active Section Content */}
          <div className="flex-1 w-full min-w-0">
            {activeSection === 'account' && (
              <div className="space-y-8 animate-fade-in">
                {/* Profile Header Card */}
                <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-md overflow-hidden shadow-2xl">
                  <div className="h-32 bg-gradient-to-r from-blue-600/20 via-purple-600/20 to-blue-600/20 relative">
                    <div className="absolute inset-0 opacity-30 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]" />
                  </div>
                  <CardContent className="p-8 -mt-16 relative">
                    <div className="flex flex-col md:flex-row items-center md:items-end gap-6">
                      <Avatar className="h-32 w-32 border-4 border-[#0a0f1d] shadow-2xl">
                        <AvatarImage src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.name || 'User'}`} />
                        <AvatarFallback className="bg-slate-800 text-3xl font-bold text-blue-400">
                          {user?.name ? getInitials(user.name) : <UserIcon className="h-12 w-12" />}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 text-center md:text-left pb-2">
                        <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-4">
                          <h1 className="text-4xl font-bold text-white tracking-tight">{user?.name || 'Quantum Explorer'}</h1>
                          <Badge className={`w-fit mx-auto md:mx-0 ${role === 'root' ? 'bg-blue-500 hover:bg-blue-600' : 'bg-slate-700'}`}>
                            {role?.toUpperCase() || 'USER'}
                          </Badge>
                        </div>
                        <p className="text-slate-400 mt-1 flex items-center justify-center md:justify-start gap-2">
                          <Shield className="h-3.5 w-3.5" />
                          {user?.email}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                  {/* Main Content (Left/Center) */}
                  <div className="md:col-span-2 space-y-8">
                    <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-md shadow-lg">
                      <CardHeader className="flex flex-row items-center gap-3">
                        <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                          <BookOpen className="h-5 w-5" />
                        </div>
                        <CardTitle className="text-xl text-white font-syne">Learning Progress</CardTitle>
                      </CardHeader>
                      <CardContent>
                        {progress.length === 0 ? (
                          <div className="text-slate-500 py-4 text-center border-2 border-dashed border-slate-800 rounded-xl">
                            No pages marked as read yet. Start your journey in the Learn section!
                          </div>
                        ) : (
                          <div className="space-y-3">
                            {progress.map(p => (
                              <div key={p.page_key} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30 border border-slate-700/50 hover:bg-slate-800/50 transition-colors group">
                                <div className="flex items-center gap-3">
                                  <div className="h-2 w-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
                                  <span className="text-slate-200 font-medium capitalize">{p.page_key.replace(/-/g, ' ')}</span>
                                </div>
                                <div className="text-xs text-slate-500 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                  <Calendar className="h-3 w-3" />
                                  {new Date(p.read_at).toLocaleDateString()}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>

                    {role === 'root' && (
                      <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-md shadow-lg">
                        <CardHeader className="flex flex-row items-center gap-3">
                          <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                            <Bell className="h-5 w-5" />
                          </div>
                          <CardTitle className="text-xl text-white font-syne">Notify Me Requests</CardTitle>
                        </CardHeader>
                        <CardContent>
                          {loadingNotifications ? (
                            <div className="flex justify-center py-8">
                              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500" />
                            </div>
                          ) : notifications.length === 0 ? (
                            <div className="text-slate-500 py-4 text-center border-2 border-dashed border-slate-800 rounded-xl">
                              No requests yet.
                            </div>
                          ) : (
                            <div className="space-y-4">
                              {notifications.map((n: any) => (
                                <div key={n.id} className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/50 flex flex-col gap-2">
                                  <div className="flex justify-between items-start">
                                    <span className="text-purple-400 font-bold text-sm tracking-tight">{n.email}</span>
                                    <span className="text-[10px] text-slate-600 font-mono">ID: {n.id}</span>
                                  </div>
                                  <p className="text-slate-300 text-sm italic">"{n.message}"</p>
                                  {n.created_at && (
                                    <div className="text-[10px] text-slate-500 mt-2 flex items-center gap-1">
                                      <Calendar className="h-3 w-3" />
                                      {new Date(n.created_at).toLocaleString()}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    )}
                  </div>

                  {/* Sidebar (Right) */}
                  <div className="space-y-8">
                    <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-md shadow-lg">
                      <CardHeader>
                        <CardTitle className="text-sm uppercase tracking-widest text-slate-500 font-syne">Account Stats</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4 font-mono text-xs">
                        <div className="flex justify-between items-center py-2 border-b border-slate-800">
                          <span className="text-slate-400">Completed Modules</span>
                          <span className="text-white font-bold">{progress.length}</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-slate-800">
                          <span className="text-slate-400">Community Rank</span>
                          <span className="text-blue-400 font-bold">Initiate</span>
                        </div>
                        <div className="pt-2">
                          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                            <div
                              className="bg-blue-500 h-full rounded-full shadow-[0_0_10px_rgba(59,130,246,0.5)]"
                              style={{ width: `${Math.min(progress.length * 10, 100)}%` }}
                            />
                          </div>
                          <p className="text-[10px] text-slate-650 mt-2 uppercase font-bold tracking-tighter text-right font-sans">Progress to next rank</p>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-md shadow-lg">
                      <CardHeader>
                        <CardTitle className="text-sm uppercase tracking-widest text-slate-500 font-syne">Account Details</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4 font-mono text-xs">
                        <div className="flex justify-between items-center py-2 border-b border-slate-800">
                          <span className="text-slate-400">Plan Tier</span>
                          <Badge variant="outline" className="text-emerald-400 border-emerald-500/30 bg-emerald-500/10 capitalize font-semibold text-[10px] tracking-wide">
                            {subscriptionPlan || 'free'}
                          </Badge>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-slate-800">
                          <span className="text-slate-400">Email Status</span>
                          <Badge variant="outline" className={session?.email_verified ? "text-cyan-400 border-cyan-500/30 bg-cyan-500/10 text-[10px]" : "text-amber-400 border-amber-500/30 bg-amber-500/10 text-[10px]"}>
                            {session?.email_verified ? 'Verified' : 'Unverified'}
                          </Badge>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-slate-800">
                          <span className="text-slate-400">Joined</span>
                          <span className="text-white text-xs font-mono font-medium">
                            {session?.created_at ? new Date(session.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between items-center py-2">
                          <span className="text-slate-400">Account ID</span>
                          <span className="text-slate-500 text-[10px] font-mono select-all">{session?.id ?? 'N/A'}</span>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Live Cohort Promotion Card */}
                    <Card className="bg-gradient-to-br from-slate-900/60 to-purple-900/40 border-slate-800 backdrop-blur-md shadow-lg overflow-hidden group hover:border-purple-500/40 transition-all duration-300">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-xs uppercase tracking-widest text-purple-400 font-syne flex items-center gap-1.5">
                          <Zap className="h-3 w-3 animate-pulse text-purple-400" />
                          Live Cohort Training
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <p className="text-xs text-slate-350 leading-relaxed font-sans">
                          Elevate your skills in our upcoming 8-week **Applied Quantum Software Engineering** cohort program.
                        </p>
                        <button
                          onClick={() => navigate('/learn')}
                          className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-mono text-xs font-semibold shadow-lg shadow-purple-500/10 transition-all duration-200"
                        >
                          <span>Explore & Enroll</span>
                          <ArrowRight className="h-3 w-3" />
                        </button>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </div>
            )}

            {activeSection === 'overview' && (
              <div className="p-6 bg-slate-900/40 backdrop-blur-xl border border-slate-850/80 rounded-2xl animate-fade-in shadow-2xl">
                <OverviewTab />
              </div>
            )}

            {activeSection === 'developer' && (
              <div className="p-6 bg-slate-900/40 backdrop-blur-xl border border-slate-850/80 rounded-2xl animate-fade-in shadow-2xl">
                <DeveloperConsoleTab />
              </div>
            )}

            {activeSection === 'billing' && (
              <div className="p-6 bg-slate-900/40 backdrop-blur-xl border border-slate-850/80 rounded-2xl animate-fade-in shadow-2xl">
                <BillingTab />
              </div>
            )}

            {activeSection === 'apidocs' && (
              <div className="p-6 bg-slate-900/40 backdrop-blur-xl border border-slate-850/80 rounded-2xl animate-fade-in shadow-2xl">
                <ApiDocsTab />
              </div>
            )}

            {activeSection === 'settings' && (
              <div className="p-6 bg-slate-900/40 backdrop-blur-xl border border-slate-850/80 rounded-2xl animate-fade-in shadow-2xl font-sans">
                <SettingsTab />
              </div>
            )}
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Profile;
