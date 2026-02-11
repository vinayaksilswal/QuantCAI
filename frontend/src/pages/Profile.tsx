import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { useAuth } from '@/hooks/useAuth';
import { BookOpen, Bell, Shield, User as UserIcon, Calendar } from 'lucide-react';

const API_BASE = (import.meta.env.VITE_API_URL as string) || "http://localhost:8000";

const Profile = () => {
  const { user, role } = useAuth();
  const [progress, setProgress] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loadingNotifications, setLoadingNotifications] = useState(false);

  useEffect(() => {
    const load = async () => {
      if (!user) return;
      const { data } = await supabase.from('page_progress').select('page_key, read_at').eq('user_id', user.id).order('read_at', { ascending: false });
      setProgress(data ?? []);
    };
    load();
  }, [user]);

  useEffect(() => {
    const loadNotifications = async () => {
      if (role !== 'root') return;
      try {
        setLoadingNotifications(true);
        const res = await fetch(`${API_BASE}/api/notify`);
        if (!res.ok) throw new Error('failed');
        const data = await res.json();
        setNotifications(data ?? []);
      } catch (err) {
        setNotifications([]);
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
    <div className="min-h-screen relative bg-[#0a0f1d]">
      <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 via-transparent to-purple-500/5 pointer-events-none" />
      <Navbar />

      <div className="pt-32 pb-20 px-6 max-w-4xl mx-auto relative z-10">
        {/* Profile Header Card */}
        <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-md mb-8 overflow-hidden">
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
            <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-md">
              <CardHeader className="flex flex-row items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                  <BookOpen className="h-5 w-5" />
                </div>
                <CardTitle className="text-xl text-white">Learning Progress</CardTitle>
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
              <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-md">
                <CardHeader className="flex flex-row items-center gap-3">
                  <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                    <Bell className="h-5 w-5" />
                  </div>
                  <CardTitle className="text-xl text-white">Notify Me Requests</CardTitle>
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
            <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-md">
              <CardHeader>
                <CardTitle className="text-sm uppercase tracking-widest text-slate-500">Account Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center py-2 border-b border-slate-800">
                  <span className="text-slate-400 text-sm">Completed Modules</span>
                  <span className="text-white font-bold">{progress.length}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-slate-800">
                  <span className="text-slate-400 text-sm">Community Rank</span>
                  <span className="text-blue-400 font-bold">Initiate</span>
                </div>
                <div className="pt-2">
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-blue-500 h-full rounded-full shadow-[0_0_10px_rgba(59,130,246,0.5)]"
                      style={{ width: `${Math.min(progress.length * 10, 100)}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-slate-600 mt-2 uppercase font-bold tracking-tighter text-right">Progress to next rank</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Profile;



