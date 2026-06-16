import { useState, useEffect } from 'react';
import { Sparkles, Shield, Cpu, BookOpen, FileText, Check, X } from 'lucide-react';
import { CheckoutButton } from '@/components/CheckoutButton';

export function UpgradeModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [reason, setReason] = useState<string | null>(null);

  useEffect(() => {
    const handleShowModal = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      setReason(detail?.reason || null);
      setIsOpen(true);
    };
    window.addEventListener('show-upgrade-modal', handleShowModal);
    return () => {
      window.removeEventListener('show-upgrade-modal', handleShowModal);
    };
  }, []);

  const getReasonInfo = () => {
    switch (reason) {
      case 'qubits':
        return {
          highlight: "Qubits capacity limit exceeded",
          desc: "You attempted to use more than 5 qubits on the visual canvas. Upgrade to Pro to simulate up to 30 qubits."
        };
      case 'depth':
        return {
          highlight: "Circuit depth limit reached",
          desc: "You attempted to design a circuit deeper than 15 gates. Upgrade to Pro for unlimited circuit depth."
        };
      case 'shots':
        return {
          highlight: "Simulation shots limit exceeded",
          desc: "You requested more than 1,024 shots. Upgrade to Pro to execute up to 65,536 shots per run."
        };
      case 'noise':
        return {
          highlight: "Noise model locked",
          desc: "You selected an advanced noise model (thermal/depolarizing). Upgrade to Pro to simulate realistic quantum hardware noise."
        };
      case 'chats':
        return {
          highlight: "Daily AI messages exceeded",
          desc: "You used all 10 free daily chats. Upgrade to Pro for unlimited, context-aware AI queries with active workspace integration."
        };
      case 'pqc':
        return {
          highlight: "Monthly PQC scans limit reached",
          desc: "You completed 5 scans this month. Upgrade to Pro for up to 100 domain scans and downloadable compliance reports."
        };
      default:
        return {
          highlight: "Unlock premium quantum tools",
          desc: "Upgrade your workspace to Pro for 25x more capacity, advanced noise simulation, PQC infrastructure tools, and personalized AI training."
        };
    }
  };

  const reasonInfo = getReasonInfo();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
      <div 
        className="relative w-full max-w-lg overflow-hidden border border-qc-accent/30 rounded-xl bg-qc-surface/90 text-qc-text p-6 shadow-2xl animate-fade-in"
        style={{
          boxShadow: '0 0 40px rgba(0, 212, 170, 0.15)',
        }}
      >
        {/* Glow overlay */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-qc-accent/10 rounded-full blur-3xl pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={() => setIsOpen(false)}
          className="absolute top-4 right-4 p-1 text-qc-muted hover:text-qc-text hover:bg-qc-border rounded transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded bg-qc-accent/15 text-qc-accent">
            <Sparkles className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold tracking-widest text-qc-accent uppercase">QuantCAI Premium</span>
            <h2 className="font-syne font-bold text-2xl">Unlock Quantum Pro</h2>
          </div>
        </div>

        {reasonInfo.highlight && (
          <div className="mb-4 p-2.5 rounded bg-qc-accent/10 border border-qc-accent/20 text-qc-accent text-xs font-mono font-bold uppercase tracking-wider text-center">
            🔒 {reasonInfo.highlight}
          </div>
        )}

        <p className="text-sm text-qc-muted mb-6 leading-relaxed">
          {reasonInfo.desc}
        </p>

        {/* Features List */}
        <div className="space-y-3.5 mb-8">
          <div className="flex items-start gap-3">
            <div className="p-1 rounded-full bg-qc-accent/20 text-qc-accent mt-0.5">
              <Check className="w-3.5 h-3.5" />
            </div>
            <div>
              <p className="text-sm font-semibold flex items-center gap-2">
                <Cpu className="w-4 h-4 text-qc-muted" />
                Advanced Noise Simulation
              </p>
              <p className="text-xs text-qc-muted mt-0.5">Simulate actual quantum hardware noise (thermal, depolarizing) with up to 65,536 shots.</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="p-1 rounded-full bg-qc-accent/20 text-qc-accent mt-0.5">
              <Check className="w-3.5 h-3.5" />
            </div>
            <div>
              <p className="text-sm font-semibold flex items-center gap-2">
                <Shield className="w-4 h-4 text-qc-muted" />
                Enhanced PQC Scans
              </p>
              <p className="text-xs text-qc-muted mt-0.5">Run up to 50 complex TLS certificate scans per month to identify cryptographic threats.</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="p-1 rounded-full bg-qc-accent/20 text-qc-accent mt-0.5">
              <Check className="w-3.5 h-3.5" />
            </div>
            <div>
              <p className="text-sm font-semibold flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-qc-muted" />
                Locked AI Quantum Tutor
              </p>
              <p className="text-xs text-qc-muted mt-0.5">Full access to custom AI training and tutorial support for OpenQASM development.</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="p-1 rounded-full bg-qc-accent/20 text-qc-accent mt-0.5">
              <Check className="w-3.5 h-3.5" />
            </div>
            <div>
              <p className="text-sm font-semibold flex items-center gap-2">
                <FileText className="w-4 h-4 text-qc-muted" />
                CBOM PDF Exporter
              </p>
              <p className="text-xs text-qc-muted mt-0.5">Export certified compliance reports outlining cryptographic assets and dependencies.</p>
            </div>
          </div>
        </div>

        {/* CTA Actions */}
        <div className="flex flex-col gap-3">
          <CheckoutButton
            amount={27}
            currency="USD"
            planName="pro"
            className="w-full py-3 text-sm"
          >
            Upgrade to Pro — $27/mo
          </CheckoutButton>

          <a
            href="mailto:sales@quantcai.in?subject=QuantCAI%20Enterprise%20Compliance%20Inquiry"
            className="w-full py-3 text-sm text-center font-semibold rounded bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 hover:brightness-110 shadow-lg transition-all"
            onClick={() => setIsOpen(false)}
          >
            Contact Sales for Enterprise
          </a>
          
          <button
            onClick={() => setIsOpen(false)}
            className="w-full py-2.5 rounded border border-qc-border text-qc-muted text-xs hover:text-qc-text hover:bg-qc-border/40 transition-colors"
          >
            Maybe Later
          </button>
        </div>
      </div>
    </div>
  );
}
