import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from "@/components/ui/card";
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { useAuth } from '@/context/AuthContext';

const API_BASE = "http://localhost:8000";

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
  return (
    <div className="min-h-screen relative">
      <Navbar />
      <div className="pt-32 pb-20 px-6 max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-6">Your Profile</h1>
        <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
          <CardContent className="p-6 text-gray-300">
            <div className="mb-4">Logged in as: <span className="text-white font-medium">{user?.email}</span> ({role ?? 'guest'})</div>
            <h3 className="text-xl font-semibold text-white mb-2">Learning Progress</h3>
            {progress.length === 0 ? (
              <div>No pages marked as read yet.</div>
            ) : (
              <ul className="list-disc pl-5 text-gray-300">
                {progress.map(p => (
                  <li key={p.page_key}>{p.page_key}</li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {role === 'root' && (
          <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm mt-6">
            <CardContent className="p-6 text-gray-300">
              <h3 className="text-xl font-semibold text-white mb-2">Notify Me requests</h3>
              {loadingNotifications ? (
                <div>Loading...</div>
              ) : notifications.length === 0 ? (
                <div>No requests yet.</div>
              ) : (
                <ul className="space-y-3">
                  {notifications.map((n: any) => (
                    <li key={n.id} className="p-3 rounded-lg bg-slate-900/60 border border-slate-700/50">
                      <div className="text-white font-medium">{n.email}</div>
                      <div className="text-gray-300 text-sm whitespace-pre-wrap">{n.message}</div>
                      {n.created_at && (
                        <div className="text-gray-500 text-xs mt-1">{new Date(n.created_at).toLocaleString()}</div>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        )}
      </div>
      <Footer />
    </div>
  );
};

export default Profile;


