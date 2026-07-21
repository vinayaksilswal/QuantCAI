import { useState, useEffect } from 'react';
import { axiosClient } from '@/lib/axiosClient';
import { toast } from 'sonner';
import { 
  Key, Plus, Trash2, Copy, Check, ShieldAlert, AlertTriangle, 
  Wallet, Coins, BarChart3, Activity, Loader2, ArrowUpRight
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

interface APIKey {
  id: number;
  name: string;
  prefix: string;
  is_active: boolean;
  created_at: string;
}

interface Wallet {
  balance_credits: number;
  auto_topup_enabled: boolean;
}

interface UsageData {
  date: string;
  requests: number;
  shots: number;
  spend: number;
}

export function DeveloperConsoleTab() {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [wallet, setWallet] = useState<Wallet>({ balance_credits: 0.0, auto_topup_enabled: false });
  const [usage, setUsage] = useState<UsageData[]>([]);
  
  const [loadingKeys, setLoadingKeys] = useState(true);
  const [loadingWallet, setLoadingWallet] = useState(true);
  const [loadingUsage, setLoadingUsage] = useState(true);
  const [topupAmount, setTopupAmount] = useState('');
  const [submittingTopup, setSubmittingTopup] = useState(false);
  
  const [modalOpen, setModalOpen] = useState(false);
  const [keyName, setKeyName] = useState('');
  const [generatingKey, setGeneratingKey] = useState(false);
  const [newKeyDetails, setNewKeyDetails] = useState<{ api_key: string; name: string } | null>(null);
  const [copied, setCopied] = useState(false);

  const [ibmKey, setIbmKey] = useState(localStorage.getItem('ibm_quantum_key') || '');
  const [ionqKey, setIonqKey] = useState(localStorage.getItem('ionq_api_key') || '');

  const fetchKeys = async () => {
    try {
      const response = await axiosClient.get<APIKey[]>('/api/v1/developer/keys');
      setKeys(response.data);
    } catch (error) {
      console.error('Error fetching API keys:', error);
      toast.error('Failed to load API keys.');
    } finally {
      setLoadingKeys(false);
    }
  };

  const fetchWallet = async () => {
    try {
      const response = await axiosClient.get<Wallet>('/api/v1/developer/wallet');
      setWallet(response.data);
    } catch (error) {
      console.error('Error fetching wallet balance:', error);
      toast.error('Failed to load wallet details.');
    } finally {
      setLoadingWallet(false);
    }
  };

  const fetchUsage = async () => {
    try {
      const response = await axiosClient.get<UsageData[]>('/api/v1/developer/usage');
      setUsage(response.data);
    } catch (error) {
      console.error('Error fetching API usage data:', error);
      toast.error('Failed to load usage statistics.');
    } finally {
      setLoadingUsage(false);
    }
  };

  useEffect(() => {
    fetchKeys();
    fetchWallet();
    fetchUsage();

    // Check for PayPal Topup redirect parameters
    const searchParams = new URLSearchParams(window.location.search);
    const topupStatus = searchParams.get('topup');
    const orderToken = searchParams.get('token');

    if (topupStatus === 'success' && orderToken) {
      const captureTopup = async () => {
        toast.info('Capturing PayPal deposit... Please do not close this window.');
        try {
          const amtParam = searchParams.get('amt');
          const mockAmount = amtParam ? parseFloat(amtParam) : 10.00;
          
          setTimeout(() => {
            setWallet((prev: any) => {
              if (!prev) return prev;
              return {
                ...prev,
                balance_credits: parseFloat((prev.balance_credits || 0).toString()) + mockAmount
              };
            });
            toast.success('Credits successfully deposited into your wallet!');
            
            // Clear query params from URL without refreshing
            const cleanUrl = window.location.pathname;
            window.history.replaceState({}, document.title, cleanUrl);
            
            // Refresh usage graph
            fetchUsage();
          }, 1500);
        } catch (err: any) {
          console.error('Capture top-up error:', err);
          const msg = err.response?.data?.detail || 'Failed to capture PayPal deposit.';
          toast.error(msg);
        }
      };
      captureTopup();
    } else if (topupStatus === 'cancel') {
      toast.warning('PayPal deposit cancelled.');
      const cleanUrl = window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
    }
  }, []);

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyName.trim()) return;

    setGeneratingKey(true);
    try {
      const response = await axiosClient.post<{ id: number; api_key: string; name: string }>('/api/v1/developer/keys', {
        name: keyName.trim(),
      });
      setNewKeyDetails({
        api_key: response.data.api_key,
        name: response.data.name,
      });
      setKeyName('');
      fetchKeys();
      toast.success('Developer API Key generated successfully!');
    } catch (error: any) {
      console.error('Error generating key:', error);
      const msg = error.response?.data?.detail || 'Failed to generate key.';
      toast.error(msg);
    } finally {
      setGeneratingKey(false);
    }
  };

  const handleToggleKey = async (id: number, currentStatus: boolean) => {
    try {
      await axiosClient.patch(`/api/v1/developer/keys/${id}`, {
        is_active: !currentStatus
      });
      toast.success(`Key ${!currentStatus ? 'activated' : 'deactivated'} successfully.`);
      fetchKeys();
    } catch (error) {
      console.error('Error toggling key status:', error);
      toast.error('Failed to update key status.');
    }
  };

  const handleDeleteKey = async (id: number) => {
    if (!confirm('Are you sure you want to revoke this API key? Systems integrated with this key will immediately start failing.')) {
      return;
    }

    try {
      await axiosClient.delete(`/api/v1/developer/keys/${id}`);
      toast.success('API key permanently revoked.');
      fetchKeys();
    } catch (error) {
      console.error('Error revoking key:', error);
      toast.error('Failed to revoke API key.');
    }
  };

  const handleCopyKey = () => {
    if (!newKeyDetails) return;
    navigator.clipboard.writeText(newKeyDetails.api_key);
    setCopied(true);
    toast.success('Copied API Key to clipboard.');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleToggleAutoTopup = async (checked: boolean) => {
    try {
      const response = await axiosClient.patch<Wallet>('/api/v1/developer/wallet', {
        auto_topup_enabled: checked
      });
      setWallet(response.data);
      toast.success(`Auto-Topup ${checked ? 'enabled' : 'disabled'} successfully.`);
    } catch (error) {
      console.error('Error updating auto-topup settings:', error);
      toast.error('Failed to update wallet settings.');
    }
  };

  const handleTopup = async (e: React.FormEvent) => {
    e.preventDefault();
    const amountFloat = parseFloat(topupAmount);
    if (isNaN(amountFloat) || amountFloat <= 0) {
      toast.error('Please enter a valid positive amount.');
      return;
    }

    setSubmittingTopup(true);
    try {
      setTimeout(() => {
        const cleanUrl = window.location.pathname;
        window.location.href = `${cleanUrl}?topup=success&token=mock-paypal-${Date.now()}&amt=${amountFloat}`;
      }, 800);
    } catch (error: any) {
      console.error('Error processing topup:', error);
      const msg = error.response?.data?.detail || 'Top-up initiation failed.';
      toast.error(msg);
    } finally {
      setSubmittingTopup(false);
    }
  };

  const closeKeyModal = () => {
    setNewKeyDetails(null);
    setModalOpen(false);
  };

  const handleSaveHardwareKeys = () => {
    localStorage.setItem('ibm_quantum_key', ibmKey);
    localStorage.setItem('ionq_api_key', ionqKey);
    toast.success('Hardware BYOK API keys saved successfully!');
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Console Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight font-syne bg-gradient-to-r from-blue-400 via-indigo-200 to-purple-400 bg-clip-text text-transparent">
            Developer Control Console
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Configure and meter your Pay-As-You-Go quantum simulation access, API keys, and micro-billing pipelines.
          </p>
        </div>
        <Badge className="w-fit bg-blue-500/10 text-blue-400 border border-blue-500/30 flex items-center gap-1.5 px-3 py-1 font-mono text-xs">
          <Activity className="w-3.5 h-3.5 animate-pulse" />
          API STATUS: OPERATIONAL
        </Badge>
      </div>

      {/* Dashboard Cards Grid (Billing & Metering) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Wallet Balance & Simulated Stripe Panel (Left: 5 cols) */}
        <Card className="lg:col-span-5 bg-slate-900/60 border-slate-800 backdrop-blur-xl shadow-2xl flex flex-col justify-between">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400 border border-blue-500/25">
                <Wallet className="w-5 h-5" />
              </div>
              <div>
                <CardTitle className="text-lg text-white font-syne">Wallet Credits</CardTitle>
                <CardDescription className="text-slate-400 text-xs">
                  Current balance and auto-reload parameters.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            
            {/* Balance Badge */}
            <div className="flex items-baseline justify-between p-4 rounded-xl bg-slate-950/40 border border-slate-800/80">
              <span className="text-xs font-mono text-slate-400 uppercase tracking-widest">Available Credits</span>
              {loadingWallet ? (
                <Loader2 className="w-6 h-6 animate-spin text-blue-400" />
              ) : (
                <span className="text-3xl font-bold text-emerald-400 font-mono tracking-tight flex items-center gap-2">
                  ${wallet.balance_credits.toFixed(4)}
                  <Badge className="bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-mono text-[10px]">USD</Badge>
                </span>
              )}
            </div>

            {/* Auto Topup Toggle */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-slate-950/20 border border-slate-800/30">
              <div className="space-y-0.5">
                <span className="text-xs font-mono text-slate-200">Auto-Topup Loader</span>
                <p className="text-[10px] text-slate-400">Instantly topup $10.00 when balance drops below $0.50.</p>
              </div>
              <Switch 
                checked={wallet.auto_topup_enabled} 
                onCheckedChange={handleToggleAutoTopup}
                disabled={loadingWallet}
              />
            </div>

            {/* Deposit Form */}
            <form onSubmit={handleTopup} className="space-y-3 pt-2">
              <label className="text-[10px] font-mono font-bold tracking-wide uppercase text-slate-500">Inject Simulated Credits</label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Coins className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
                  <Input 
                    type="number" 
                    step="0.01" 
                    placeholder="Amount (e.g. 10.00)" 
                    value={topupAmount}
                    onChange={(e) => setTopupAmount(e.target.value)}
                    className="pl-9 bg-slate-950 border-slate-800 font-mono text-xs focus-visible:ring-blue-500 text-white"
                    disabled={submittingTopup}
                  />
                </div>
                <Button 
                  type="submit" 
                  disabled={submittingTopup} 
                  className="bg-blue-600 hover:bg-blue-700 text-white font-mono text-xs flex items-center gap-1 px-4"
                >
                  {submittingTopup ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ArrowUpRight className="w-3.5 h-3.5" />}
                  Top-Up
                </Button>
              </div>
              <p className="text-[9px] text-slate-500 italic">Simulates a PayPal callback. Credited to test wallet.</p>
            </form>

          </CardContent>
        </Card>

        {/* Recharts API Consumption Dashboard (Right: 7 cols) */}
        <Card className="lg:col-span-7 bg-slate-900/60 border-slate-800 backdrop-blur-xl shadow-2xl">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400 border border-purple-500/25">
                  <BarChart3 className="w-5 h-5" />
                </div>
                <div>
                  <CardTitle className="text-lg text-white font-syne">API Usage & Spend</CardTitle>
                  <CardDescription className="text-slate-400 text-xs">
                    Rolling 30-day overview of execution costs and query volume.
                  </CardDescription>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="h-64 sm:h-80 pb-6">
            {loadingUsage ? (
              <div className="w-full h-full flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={usage} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={9} tickLine={false} />
                  <YAxis yAxisId="left" stroke="#60a5fa" fontSize={9} tickLine={false} />
                  <YAxis yAxisId="right" orientation="right" stroke="#c084fc" fontSize={9} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#fff', fontSize: '11px', fontFamily: 'monospace' }}
                    labelStyle={{ color: '#94a3b8', fontWeight: 'bold' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '10px', fontFamily: 'monospace', paddingTop: '10px' }} />
                  <Bar yAxisId="left" dataKey="requests" name="Queries" fill="#3b82f6" radius={[4, 4, 0, 0]} maxBarSize={25} />
                  <Bar yAxisId="right" dataKey="spend" name="Spend ($)" fill="#a855f7" radius={[4, 4, 0, 0]} maxBarSize={25} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* API Key Manager Panel */}
      <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-xl shadow-2xl">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <CardTitle className="text-xl text-white font-syne flex items-center gap-2">
              <Key className="w-5 h-5 text-blue-400" />
              API Credentials
            </CardTitle>
            <CardDescription className="text-slate-400 text-xs mt-1">
              Generate keys to authenticate your micro-billing circuit simulations. Keep your secret key hidden.
            </CardDescription>
          </div>
          <Button 
            onClick={() => setModalOpen(true)}
            className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-mono text-xs flex items-center gap-1.5 self-start sm:self-center"
          >
            <Plus className="w-4 h-4" />
            Generate New Key
          </Button>
        </CardHeader>

        <CardContent className="p-0">
          {loadingKeys ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
              <p className="text-xs text-slate-500 font-mono">Fetching active credentials...</p>
            </div>
          ) : keys.length === 0 ? (
            <div className="p-12 text-center text-sm text-slate-500 font-mono border-dashed border-2 border-slate-800/80 m-6 rounded-2xl">
              No developer API keys found. Generate a key to begin public API integration.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-500 bg-slate-950/20">
                    <th className="px-6 py-4 font-semibold">Label Name</th>
                    <th className="px-6 py-4 font-semibold">Key Identifier</th>
                    <th className="px-6 py-4 font-semibold">Created Date</th>
                    <th className="px-6 py-4 font-semibold">Status</th>
                    <th className="px-6 py-4 font-semibold text-right">Access Controls</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40">
                  {keys.map((k) => (
                    <tr key={k.id} className="hover:bg-slate-800/10 transition-colors">
                      <td className="px-6 py-4 text-white font-semibold flex items-center gap-2">
                        <Key className="w-4 h-4 text-slate-500" />
                        {k.name}
                      </td>
                      <td className="px-6 py-4 text-blue-400">
                        {k.prefix}••••••••••••
                      </td>
                      <td className="px-6 py-4 text-slate-400">
                        {new Date(k.created_at).toLocaleDateString(undefined, {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric'
                        })}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${
                          k.is_active ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'
                        }`}>
                          {k.is_active ? 'ACTIVE' : 'DEACTIVATED'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right space-x-3">
                        <button
                          onClick={() => handleToggleKey(k.id, k.is_active)}
                          className={`px-2 py-1 rounded text-[10px] font-bold border transition-colors ${
                            k.is_active 
                              ? 'bg-slate-850 text-slate-400 hover:text-white border-slate-800' 
                              : 'bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 border-blue-500/20'
                          }`}
                        >
                          {k.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button
                          onClick={() => handleDeleteKey(k.id)}
                          className="p-1.5 rounded text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-colors inline-flex align-middle"
                          title="Revoke Key"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Hardware BYOK Panel */}
      <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-xl shadow-2xl">
        <CardHeader className="border-b border-slate-800 pb-5">
          <CardTitle className="text-xl text-white font-syne flex items-center gap-2">
            <Key className="w-5 h-5 text-emerald-400" />
            Hardware Provider BYOK (Bring Your Own Key)
          </CardTitle>
          <CardDescription className="text-slate-400 text-xs mt-1">
            Provide your own API keys to run simulations directly on third-party cloud hardware. Keys are stored securely in your browser's local storage.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-[10px] font-mono font-bold tracking-wide uppercase text-slate-500">IBM Quantum API Key</label>
              <Input
                type="password"
                placeholder="Enter IBM Quantum token"
                value={ibmKey}
                onChange={(e) => setIbmKey(e.target.value)}
                className="bg-slate-950 border-slate-800 text-white text-xs font-mono"
              />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-mono font-bold tracking-wide uppercase text-slate-500">IonQ API Key</label>
              <Input
                type="password"
                placeholder="Enter IonQ API key"
                value={ionqKey}
                onChange={(e) => setIonqKey(e.target.value)}
                className="bg-slate-950 border-slate-800 text-white text-xs font-mono"
              />
            </div>
          </div>
          <Button 
            onClick={handleSaveHardwareKeys}
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-mono text-xs px-6"
          >
            Save BYOK Keys
          </Button>
        </CardContent>
      </Card>

      {/* Secret API Key Generation Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
          <div className="relative w-full max-w-md overflow-hidden border border-slate-800 rounded-2xl bg-slate-900 p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-250">
            
            {!newKeyDetails ? (
              <form onSubmit={handleCreateKey} className="space-y-4">
                <h3 className="font-syne font-bold text-lg text-white">Create Developer API Key</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Specify a descriptive label to recognize this credential.Plaintext secret keys will only be shown once on successful generation.
                </p>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-mono font-bold tracking-wide uppercase text-slate-500">Key Name</label>
                  <Input
                    type="text"
                    placeholder="e.g. Quant Simulator Server"
                    value={keyName}
                    onChange={(e) => setKeyName(e.target.value)}
                    className="bg-slate-950 border-slate-800 text-white text-xs font-mono"
                    required
                    disabled={generatingKey}
                  />
                </div>

                <div className="flex gap-3 pt-2">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setModalOpen(false)}
                    disabled={generatingKey}
                    className="flex-1 hover:bg-slate-800 text-slate-400 text-xs"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={generatingKey}
                    className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-mono text-xs"
                  >
                    {generatingKey ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Generate Key'}
                  </Button>
                </div>
              </form>
            ) : (
              <div className="space-y-5">
                <div className="flex items-center gap-2 text-red-400">
                  <ShieldAlert className="w-5 h-5 flex-shrink-0" />
                  <h3 className="font-syne font-bold text-base text-white">Secure Your Plaintext Key</h3>
                </div>

                <div className="p-3 border border-red-500/20 bg-red-500/5 rounded-xl flex items-start gap-2.5 text-[10px] text-slate-300 font-mono leading-relaxed">
                  <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5 animate-pulse" />
                  <span>
                    <strong>WARNING:</strong> This key is only displayed once. Please copy and store it securely. We do not store plaintext keys in our database and it cannot be retrieved again.
                  </span>
                </div>

                <div className="space-y-2">
                  <span className="text-[9px] font-mono font-bold text-slate-500 uppercase">Key Name: {newKeyDetails.name}</span>
                  <div className="flex gap-2">
                    <Input
                      type="text"
                      value={newKeyDetails.api_key}
                      readOnly
                      className="flex-1 bg-slate-950 border-slate-800 text-emerald-400 font-mono text-xs focus-visible:ring-0 select-all"
                    />
                    <Button
                      onClick={handleCopyKey}
                      variant="outline"
                      className="border-slate-800 hover:bg-blue-500/10 hover:border-blue-500/40 transition-colors flex items-center justify-center p-3"
                    >
                      {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                    </Button>
                  </div>
                </div>

                <Button
                  onClick={closeKeyModal}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-mono text-xs py-2.5"
                >
                  I Have Saved My Key
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
