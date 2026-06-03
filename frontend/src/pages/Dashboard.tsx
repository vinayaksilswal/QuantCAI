import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { UpgradeModal } from '@/components/UpgradeModal';
import { OverviewTab } from '@/components/dashboard/OverviewTab';
import { QuantumSimulatorTab } from '@/components/dashboard/QuantumSimulatorTab';
import { ApiKeysTab } from '@/components/dashboard/ApiKeysTab';
import { BillingTab } from '@/components/dashboard/BillingTab';
import { SettingsTab } from '@/components/dashboard/SettingsTab';
import { 
  LayoutDashboard, 
  BookOpen, 
  Cpu, 
  Key, 
  CreditCard, 
  Settings, 
  LogOut, 
  Lock,
  User
} from 'lucide-react';

interface SidebarItem {
  id: string;
  label: string;
  icon: any;
  locked?: boolean;
}

export default function Dashboard() {
  const { user, subscriptionPlan, signOut } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');

  const isFree = subscriptionPlan === 'free' || !subscriptionPlan;

  const sidebarItems: SidebarItem[] = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'ai-tutor', label: 'AI Tutor', icon: BookOpen, locked: isFree },
    { id: 'simulator', label: 'Quantum Simulator', icon: Cpu },
    { id: 'api-keys', label: 'API Keys', icon: Key },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const handleTabClick = (item: SidebarItem) => {
    if (item.locked) {
      // Trigger global upgrade modal event
      window.dispatchEvent(new CustomEvent('show-upgrade-modal'));
      return;
    }
    setActiveTab(item.id);
  };

  const handleLogout = async () => {
    try {
      await signOut();
      navigate('/login');
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  // Render active tab component
  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab />;
      case 'simulator':
        return <QuantumSimulatorTab />;
      case 'api-keys':
        return <ApiKeysTab />;
      case 'billing':
        return <BillingTab />;
      case 'settings':
        return <SettingsTab />;
      default:
        return <OverviewTab />;
    }
  };

  return (
    <div className="flex h-screen bg-qc-bg text-qc-text overflow-hidden selection:bg-qc-accent/20 selection:text-qc-accent">
      {/* Upgrade Modal Listener */}
      <UpgradeModal />

      {/* ─────────────────────────── SIDEBAR ─────────────────────────── */}
      <aside className="w-64 border-r border-qc-border bg-qc-surface flex flex-col flex-shrink-0 z-20">
        {/* Brand Logo */}
        <div className="h-16 px-6 border-b border-qc-border/60 flex items-center gap-3">
          <div className="w-8 h-8 rounded border border-qc-accent/40 flex items-center justify-center text-qc-accent font-mono text-sm font-bold">
            Q
          </div>
          <span className="font-syne font-bold text-qc-text tracking-tight text-base">QuantCAI Console</span>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          {sidebarItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => handleTabClick(item)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded font-mono text-xs transition-all ${
                  isActive 
                    ? 'bg-qc-accent/10 border-l-2 border-qc-accent text-qc-accent font-semibold' 
                    : 'text-qc-muted hover:bg-qc-border/40 hover:text-qc-text'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4.5 h-4.5 ${isActive ? 'text-qc-accent' : 'text-qc-muted'}`} />
                  <span>{item.label}</span>
                </div>
                {item.locked && (
                  <Lock className="w-3.5 h-3.5 text-qc-muted group-hover:text-qc-accent/60" />
                )}
              </button>
            );
          })}
        </nav>

        {/* User profile section bottom sidebar */}
        <div className="p-4 border-t border-qc-border/60 bg-qc-bg/30">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full border border-qc-border bg-qc-surface flex items-center justify-center text-qc-accent">
              <User className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-qc-text truncate">{user?.name || 'Workspace User'}</p>
              <p className="text-[10px] text-qc-muted truncate">{user?.email || 'user@quantcai.in'}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full py-2 rounded border border-qc-border text-qc-muted hover:text-qc-danger hover:bg-qc-danger/5 transition-all text-xs font-mono flex items-center justify-center gap-2"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* ────────────────────────── CONTENT AREA ─────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Decorative glows */}
        <div className="absolute top-1/4 left-1/3 w-[500px] h-[300px] bg-qc-accent/[0.02] rounded-full blur-[100px] pointer-events-none" />

        {/* Top Header */}
        <header className="h-16 px-8 border-b border-qc-border/60 bg-qc-surface/40 backdrop-blur-md flex items-center justify-between flex-shrink-0 z-10">
          {/* Path / Section */}
          <div className="flex items-center gap-2 font-mono text-xs text-qc-muted">
            <span>console</span>
            <span>/</span>
            <span className="text-qc-text uppercase font-bold tracking-wider">
              {sidebarItems.find(i => i.id === activeTab)?.label || 'Overview'}
            </span>
          </div>

          {/* User Status / Subscription Plan Badge */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-qc-muted font-mono uppercase">Subscription Status:</span>
              <span className={`px-2 py-0.5 rounded border text-[9px] font-mono font-bold tracking-wider uppercase ${
                subscriptionPlan === 'enterprise' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' :
                subscriptionPlan === 'pro' ? 'bg-qc-accent/10 text-qc-accent border-qc-accent/20' :
                'bg-qc-border text-qc-muted border-transparent'
              }`}>
                {subscriptionPlan ? subscriptionPlan : 'FREE'}
              </span>
            </div>
          </div>
        </header>

        {/* Tab Content (Scrollable) */}
        <main className="flex-1 overflow-y-auto p-8 relative z-10">
          <div className="max-w-5xl mx-auto">
            {renderTabContent()}
          </div>
        </main>
      </div>
    </div>
  );
}
