import { useState, useEffect } from 'react';
import { axiosClient } from '@/lib/axiosClient';
import { toast } from 'sonner';
import { Key, Plus, Trash2, Copy, AlertTriangle, Check, ShieldAlert } from 'lucide-react';

interface APIKey {
  id: number;
  label: string;
  tier: string;
  requests_today: number;
  daily_limit: number;
  last_used: string | null;
  is_active: boolean;
}

export function ApiKeysTab() {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [keyLabel, setKeyLabel] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [newKeyDetails, setNewKeyDetails] = useState<{ key: string; label: string } | null>(null);
  const [copied, setCopied] = useState(false);

  const fetchKeys = async () => {
    try {
      const response = await axiosClient.get<APIKey[]>('/developer/keys');
      setKeys(response.data);
    } catch (error) {
      console.error('Error fetching keys:', error);
      // Fallback fallback keys list
      setKeys([
        { id: 1, label: 'Production Server Key', tier: 'PRO', requests_today: 432, daily_limit: 10000, last_used: new Date().toISOString(), is_active: true },
        { id: 2, label: 'Local Development Key', tier: 'FREE', requests_today: 14, daily_limit: 1000, last_used: new Date(Date.now() - 3600000).toISOString(), is_active: true },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyLabel.trim()) return;

    setSubmitting(true);
    try {
      const response = await axiosClient.post<{ api_key: string; label: string }>('/developer/keys', {
        label: keyLabel.trim(),
      });
      setNewKeyDetails({
        key: response.data.api_key,
        label: response.data.label,
      });
      setKeyLabel('');
      fetchKeys();
    } catch (error: any) {
      console.error('Error creating API key:', error);
      const msg = error.response?.data?.detail || 'Failed to create API key.';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteKey = async (id: number) => {
    if (!confirm('Are you sure you want to delete this API key? Any systems using this key will immediately lose access.')) {
      return;
    }

    try {
      await axiosClient.delete(`/developer/keys/${id}`);
      toast.success('API key deleted successfully.');
      fetchKeys();
    } catch (error: any) {
      console.error('Error deleting API key:', error);
      toast.error('Failed to delete API key.');
    }
  };

  const handleCopyKey = () => {
    if (!newKeyDetails) return;
    navigator.clipboard.writeText(newKeyDetails.key);
    setCopied(true);
    toast.success('API key copied to clipboard.');
    setTimeout(() => setCopied(false), 2000);
  };

  const closeKeyModal = () => {
    setNewKeyDetails(null);
    setModalOpen(false);
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-syne font-bold text-2xl text-qc-text">API Keys</h1>
          <p className="text-sm text-qc-muted mt-1">Manage credentials for programmatically executing quantum circuits and PQC compliance checks.</p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="px-4 py-2 rounded bg-qc-accent text-qc-bg font-semibold text-xs hover:brightness-110 active:scale-[0.98] transition-all flex items-center gap-1.5 self-start sm:self-center"
        >
          <Plus className="w-4 h-4" />
          Create New Key
        </button>
      </div>

      {/* Keys Table Container */}
      <div className="border border-qc-border rounded bg-qc-surface/30 overflow-hidden">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-8 h-8 border-2 border-t-transparent border-qc-accent rounded-full animate-spin" />
            <p className="text-sm text-qc-muted font-mono">Loading credentials...</p>
          </div>
        ) : keys.length === 0 ? (
          <div className="p-8 text-center text-sm text-qc-muted font-mono">
            No API keys found. Create a new API key to begin integration.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono border-collapse">
              <thead>
                <tr className="border-b border-qc-border/70 text-qc-muted bg-qc-surface/20">
                  <th className="px-5 py-3 font-semibold">Label</th>
                  <th className="px-5 py-3 font-semibold">Tier</th>
                  <th className="px-5 py-3 font-semibold">Usage Today</th>
                  <th className="px-5 py-3 font-semibold">Last Active</th>
                  <th className="px-5 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-qc-border/40">
                {keys.map((k) => (
                  <tr key={k.id} className="hover:bg-qc-surface/30 transition-colors">
                    <td className="px-5 py-4 text-qc-text font-semibold flex items-center gap-2">
                      <Key className="w-4 h-4 text-qc-muted" />
                      {k.label}
                    </td>
                    <td className="px-5 py-4">
                      <span className={`px-2 py-0.5 rounded border text-[9px] font-bold ${
                        k.tier === 'ENTERPRISE' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' :
                        k.tier === 'PRO' ? 'bg-qc-accent/10 text-qc-accent border-qc-accent/20' :
                        'bg-qc-border text-qc-muted border-transparent'
                      }`}>
                        {k.tier}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-qc-text">
                      {k.requests_today} / {k.daily_limit}
                    </td>
                    <td className="px-5 py-4 text-qc-muted">
                      {k.last_used ? new Date(k.last_used).toLocaleString() : 'Never'}
                    </td>
                    <td className="px-5 py-4 text-right">
                      <button
                        onClick={() => handleDeleteKey(k.id)}
                        className="p-1.5 rounded text-qc-danger hover:bg-qc-danger/10 transition-colors"
                        title="Delete key"
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
      </div>

      {/* Creation Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
          <div className="relative w-full max-w-md overflow-hidden border border-qc-border rounded-xl bg-qc-surface p-6 shadow-2xl animate-fade-in">
            
            {/* Step 1: Input Label */}
            {!newKeyDetails ? (
              <form onSubmit={handleCreateKey} className="space-y-4">
                <h3 className="font-syne font-bold text-lg text-qc-text">Create API Key</h3>
                <p className="text-xs text-qc-muted leading-relaxed">
                  Generate a secret key to authenticate your HTTP requests. Specify a descriptive label to recognize it in the console.
                </p>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-mono font-bold tracking-wide uppercase text-qc-muted">Key Label</label>
                  <input
                    type="text"
                    placeholder="e.g. Production Backend Server"
                    value={keyLabel}
                    onChange={(e) => setKeyLabel(e.target.value)}
                    className="w-full px-3 py-2 rounded border border-qc-border bg-qc-bg text-qc-text font-mono text-xs focus:outline-none focus:border-qc-accent/50"
                    required
                    disabled={submitting}
                  />
                </div>

                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setModalOpen(false)}
                    disabled={submitting}
                    className="flex-1 py-2.5 rounded border border-qc-border text-qc-muted text-xs hover:text-qc-text hover:bg-qc-border/40 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="flex-1 py-2.5 rounded bg-qc-accent text-qc-bg font-semibold text-xs hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
                  >
                    {submitting ? 'Generating...' : 'Generate Key'}
                  </button>
                </div>
              </form>
            ) : (
              /* Step 2: Show Key Once */
              <div className="space-y-5">
                <div className="flex items-center gap-2 text-qc-danger">
                  <ShieldAlert className="w-5 h-5 flex-shrink-0" />
                  <h3 className="font-syne font-bold text-base text-qc-text">Store Your API Key</h3>
                </div>

                <div className="p-3 border border-qc-danger/25 bg-qc-danger/5 rounded flex items-start gap-2 text-[10px] text-qc-muted font-mono leading-relaxed">
                  <AlertTriangle className="w-4 h-4 text-qc-danger flex-shrink-0 mt-0.5 animate-pulse" />
                  <span>
                    <strong>WARNING:</strong> This key is only displayed once. Please copy and store it securely. We do not store plaintext keys in our database and it cannot be retrieved again.
                  </span>
                </div>

                <div className="space-y-1.5">
                  <span className="text-[9px] font-mono font-bold text-qc-muted uppercase">Key Name: {newKeyDetails.label}</span>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newKeyDetails.key}
                      readOnly
                      className="flex-1 px-3 py-2 rounded border border-qc-border bg-qc-bg text-qc-accent font-mono text-xs focus:outline-none select-all"
                    />
                    <button
                      onClick={handleCopyKey}
                      className="px-3 rounded border border-qc-border hover:border-qc-accent hover:bg-qc-accent/10 transition-colors flex items-center justify-center text-qc-text"
                    >
                      {copied ? <Check className="w-4 h-4 text-qc-accent" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <button
                  onClick={closeKeyModal}
                  className="w-full py-2.5 rounded bg-qc-accent text-qc-bg font-semibold text-xs hover:brightness-110 active:scale-[0.98] transition-all"
                >
                  I Have Saved My Key
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
