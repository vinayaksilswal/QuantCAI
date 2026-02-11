import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from "@/components/ui/card";
import { useEffect, useState } from 'react';
import { api, User } from '@/lib/api';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from '@/hooks/useAuth';

const Admin = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<'root' | 'developer' | 'user'>('developer');
  const [blockEmail, setBlockEmail] = useState('');
  const [blockReason, setBlockReason] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const data = await api.getUsers();
        setUsers(data ?? []);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to load users');
        console.error('Error loading users:', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const setUserRole = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setError(null);
    setSuccess(null);

    try {
      // TODO: Implement backend endpoint for updating user role
      // await api.updateUserRole(email, role);
      setSuccess(`Role update endpoint not yet implemented. Would update ${email} to ${role}`);
      // Refresh users list
      const data = await api.getUsers();
      setUsers(data ?? []);
      setEmail('');
    } catch (err: any) {
      setError(err.message || 'Failed to update user role');
    }
  };

  const blockUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!blockEmail) return;
    setError(null);
    setSuccess(null);

    try {
      // TODO: Implement backend endpoint for blocking users
      // await api.blockUser(blockEmail, blockReason);
      setSuccess(`Block user endpoint not yet implemented. Would block ${blockEmail}`);
      setBlockEmail('');
      setBlockReason('');
    } catch (err: any) {
      setError(err.message || 'Failed to block user');
    }
  };
  return (
    <div className="min-h-screen relative">
      <Navbar />
      <div className="pt-32 pb-20 px-6 max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-6">Admin Control</h1>
        {currentUser && (
          <div className="mb-4 text-gray-300">
            Logged in as: <span className="text-white font-semibold">{currentUser.email}</span>
            <span className="ml-2 text-blue-400">({currentUser.id})</span>
          </div>
        )}
        <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm mb-6">
          <CardContent className="p-6 text-gray-300">
            <div className="mb-4">Root-only dashboard to manage users, developers, and content.</div>
            {error && <div className="mb-4 p-3 bg-red-900/50 border border-red-700 rounded text-red-200">{error}</div>}
            {success && <div className="mb-4 p-3 bg-green-900/50 border border-green-700 rounded text-green-200">{success}</div>}
            <form onSubmit={setUserRole} className="flex gap-2 mb-6">
              <Input placeholder="User email" value={email} onChange={e => setEmail(e.target.value)} className="bg-slate-800/50 border-slate-600 text-white" required />
              <select value={role} onChange={e => setRole(e.target.value as any)} className="bg-slate-800/50 border border-slate-600 text-white rounded px-3 py-2">
                <option value="developer">developer</option>
                <option value="user">user</option>
                <option value="root">root</option>
              </select>
              <Button type="submit" className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700">Set role</Button>
            </form>
            <form onSubmit={blockUser} className="flex gap-2 mb-6">
              <Input placeholder="Block user email" value={blockEmail} onChange={e => setBlockEmail(e.target.value)} className="bg-slate-800/50 border-slate-600 text-white" required />
              <Input placeholder="Reason (optional)" value={blockReason} onChange={e => setBlockReason(e.target.value)} className="bg-slate-800/50 border-slate-600 text-white" />
              <Button type="submit" variant="destructive" className="bg-red-600 hover:bg-red-700">Block</Button>
            </form>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
          <CardContent className="p-6 text-gray-300">
            <h3 className="text-xl font-semibold text-white mb-4">Users ({users.length})</h3>
            {loading ? (
              <div className="text-gray-400">Loading users...</div>
            ) : users.length === 0 ? (
              <div className="text-gray-400">No users found</div>
            ) : (
              <div className="space-y-2">
                {users.map(u => (
                  <div key={u.id} className="flex justify-between items-center bg-slate-800/50 rounded px-3 py-2">
                    <div className="flex-1">
                      <div className="text-white font-medium">{u.email}</div>
                      <div className="text-sm text-gray-400">
                        {u.name} • Role: <span className="text-blue-400">{u.role}</span>
                        {u.is_blocked && <span className="ml-2 text-red-400">(Blocked)</span>}
                        {!u.is_active && <span className="ml-2 text-yellow-400">(Inactive)</span>}
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">ID: {u.id}</div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      <Footer />
    </div>
  );
};

export default Admin;


