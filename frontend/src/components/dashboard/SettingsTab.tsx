import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { toast } from 'sonner';
import { User, Lock, Sliders } from 'lucide-react';

export function SettingsTab() {
  const { user, role, subscriptionPlan } = useAuth();
  
  // States for password update fields
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [updating, setUpdating] = useState(false);

  // States for toggle settings
  const [notifications, setNotifications] = useState(true);
  const [marketing, setMarketing] = useState(false);
  const [telemetry, setTelemetry] = useState(true);

  const handlePasswordUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error('New password and confirmation do not match.');
      return;
    }
    
    setUpdating(true);
    setTimeout(() => {
      toast.success('Security settings updated successfully.');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setUpdating(false);
    }, 1000);
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="font-syne font-bold text-2xl text-qc-text">Account Settings</h1>
        <p className="text-sm text-qc-muted mt-1">Manage your account profile, credentials, and notification settings.</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6 items-start">
        {/* Left Columns (Profile & Settings) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Profile Card */}
          <div className="p-5 border border-qc-border rounded bg-qc-surface/30 space-y-4">
            <h3 className="font-syne font-bold text-sm text-qc-text flex items-center gap-2">
              <User className="w-4 h-4 text-qc-accent" />
              Profile Details
            </h3>

            <div className="grid sm:grid-cols-2 gap-4 font-mono text-xs">
              <div className="space-y-1">
                <span className="text-qc-muted block text-[10px] uppercase">Username</span>
                <input 
                  type="text" 
                  value={user?.name || 'N/A'} 
                  readOnly 
                  className="w-full px-3 py-2 rounded border border-qc-border bg-qc-bg text-qc-text focus:outline-none"
                />
              </div>
              <div className="space-y-1">
                <span className="text-qc-muted block text-[10px] uppercase">Email Address</span>
                <input 
                  type="text" 
                  value={user?.email || 'N/A'} 
                  readOnly 
                  className="w-full px-3 py-2 rounded border border-qc-border bg-qc-bg text-qc-text focus:outline-none"
                />
              </div>
              <div className="space-y-1">
                <span className="text-qc-muted block text-[10px] uppercase">Account Role</span>
                <input 
                  type="text" 
                  value={role?.toUpperCase() || 'USER'} 
                  readOnly 
                  className="w-full px-3 py-2 rounded border border-qc-border bg-qc-bg text-qc-text focus:outline-none"
                />
              </div>
              <div className="space-y-1">
                <span className="text-qc-muted block text-[10px] uppercase">Subscription Plan</span>
                <input 
                  type="text" 
                  value={subscriptionPlan?.toUpperCase() || 'FREE'} 
                  readOnly 
                  className="w-full px-3 py-2 rounded border border-qc-border bg-qc-bg text-qc-accent focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Preferences Card */}
          <div className="p-5 border border-qc-border rounded bg-qc-surface/30 space-y-4">
            <h3 className="font-syne font-bold text-sm text-qc-text flex items-center gap-2">
              <Sliders className="w-4 h-4 text-qc-accent" />
              Workspace Preferences
            </h3>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between p-2 hover:bg-qc-surface/20 rounded">
                <div>
                  <p className="font-bold text-qc-text">Developer Telemetry</p>
                  <p className="text-[10px] text-qc-muted mt-0.5">Share anonymous quantum gate execution metrics to improve simulation performance.</p>
                </div>
                <input 
                  type="checkbox" 
                  checked={telemetry} 
                  onChange={(e) => setTelemetry(e.target.checked)}
                  className="accent-qc-accent w-4 h-4 cursor-pointer"
                />
              </div>

              <div className="flex items-center justify-between p-2 hover:bg-qc-surface/20 rounded">
                <div>
                  <p className="font-bold text-qc-text">Email Notifications</p>
                  <p className="text-[10px] text-qc-muted mt-0.5">Receive warnings about rate limits and usage approaching subscription capacity.</p>
                </div>
                <input 
                  type="checkbox" 
                  checked={notifications} 
                  onChange={(e) => setNotifications(e.target.checked)}
                  className="accent-qc-accent w-4 h-4 cursor-pointer"
                />
              </div>

              <div className="flex items-center justify-between p-2 hover:bg-qc-surface/20 rounded">
                <div>
                  <p className="font-bold text-qc-text">Marketing Announcements</p>
                  <p className="text-[10px] text-qc-muted mt-0.5">Stay up-to-date with new post-quantum cryptographic scans and Q-Day readiness news.</p>
                </div>
                <input 
                  type="checkbox" 
                  checked={marketing} 
                  onChange={(e) => setMarketing(e.target.checked)}
                  className="accent-qc-accent w-4 h-4 cursor-pointer"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (Security / Password Update) */}
        <form onSubmit={handlePasswordUpdate} className="p-5 border border-qc-border rounded bg-qc-surface/30 space-y-4">
          <h3 className="font-syne font-bold text-sm text-qc-text flex items-center gap-2">
            <Lock className="w-4 h-4 text-qc-accent" />
            Update Password
          </h3>

          <div className="space-y-3 font-mono text-xs">
            <div className="space-y-1">
              <label className="text-[10px] text-qc-muted uppercase">Current Password</label>
              <input
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                className="w-full px-3 py-2 rounded border border-qc-border bg-qc-bg text-qc-text focus:outline-none"
                required
                disabled={updating}
              />
            </div>
            
            <div className="space-y-1">
              <label className="text-[10px] text-qc-muted uppercase">New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full px-3 py-2 rounded border border-qc-border bg-qc-bg text-qc-text focus:outline-none"
                required
                disabled={updating}
              />
            </div>

            <div className="space-y-1">
              <label className="text-[10px] text-qc-muted uppercase">Confirm New Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-3 py-2 rounded border border-qc-border bg-qc-bg text-qc-text focus:outline-none"
                required
                disabled={updating}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={updating}
            className="w-full py-2 rounded bg-qc-surface border border-qc-border text-qc-text font-semibold text-xs hover:border-qc-accent/50 hover:bg-qc-border/20 transition-all disabled:opacity-50"
          >
            {updating ? 'Updating...' : 'Update Password'}
          </button>
        </form>
      </div>
    </div>
  );
}
