import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { usePageTracking } from '@/hooks/usePageTracking';
import { Button } from '@/components/ui/button';
import {
  ArrowRight, Atom, Rocket, Settings,
  Terminal, ShieldCheck, Check,
  Landmark, Globe, Lock, Zap,
} from 'lucide-react';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { NewsletterForm } from '@/components/NewsletterForm';
import { LogoProcessor } from '@/components/LogoProcessor';
import { useAuth } from '@/hooks/useAuth';

/* ─────────────────────────── CODE SNIPPETS ─────────────────────────── */
const curlSnippet = `curl -X POST https://api.quantcai.in/v1/simulate \\
  -H "X-API-Key: qcai_your_key" \\
  -d '{
    "circuit_qasm": "OPENQASM 2.0; qreg q[2]; h q[0]; cx q[0],q[1]; measure q -> c;",
    "shots": 1024
  }'`;

const responseSnippet = `{
  "job_id": "sim_8f3k2x",
  "status": "completed",
  "counts": {
    "00": 512,
    "11": 512
  },
  "execution_time_ms": 847
}`;

/* ─────────────────────────── PRICING CARD ──────────────────────────── */
interface PlanProps {
  name: string;
  price: string;
  period?: string;
  badge?: string;
  features: string[];
  cta: string;
  ctaHref?: string;
  onClick?: () => void;
  highlighted?: boolean;
  loading?: boolean;
}

const PlanCard = ({ name, price, period, badge, features, cta, ctaHref, onClick, highlighted, loading }: PlanProps) => (
  <div
    className={`relative rounded-2xl border p-6 sm:p-8 flex flex-col backdrop-blur-xl transition-all duration-300 ${highlighted
      ? 'bg-white/10 border-cyan-400/40 shadow-2xl shadow-cyan-500/20 hover:border-cyan-400/60'
      : 'bg-white/5 border-blue-400/20 shadow-xl shadow-blue-500/10 hover:border-blue-400/40'
      }`}
  >
    {badge && (
      <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-qc-accent text-black text-[10px] font-bold tracking-wider uppercase shadow-lg shadow-cyan-500/30">
        {badge}
      </div>
    )}
    <div className="mb-6">
      <h3 className="font-bold text-lg text-white mb-1 drop-shadow-md">{name}</h3>
      <div className="flex items-baseline gap-1">
        <span className="font-extrabold text-3xl text-white drop-shadow-md">{price}</span>
        {period && <span className="text-blue-200 text-sm">/{period}</span>}
      </div>
    </div>
    <ul className="space-y-3 mb-8 flex-1">
      {features.map((f, i) => (
        <li key={i} className="flex items-start gap-2 text-sm text-blue-200">
          <Check className="w-4 h-4 text-qc-accent flex-shrink-0 mt-0.5" />
          <span>{f}</span>
        </li>
      ))}
    </ul>
    {onClick ? (
      <button
        onClick={onClick}
        disabled={loading}
        className={`block w-full text-center py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 disabled:opacity-50 ${highlighted
          ? 'bg-qc-accent text-black hover:brightness-110 shadow-lg shadow-cyan-500/25'
          : 'border border-blue-400/30 text-white hover:border-blue-400/50 hover:bg-white/10'
          }`}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-black" />
            Processing...
          </span>
        ) : cta}
      </button>
    ) : (
      <a
        href={ctaHref}
        className={`block text-center py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 ${highlighted
          ? 'bg-qc-accent text-black hover:brightness-110 shadow-lg shadow-cyan-500/25'
          : 'border border-blue-400/30 text-white hover:border-blue-400/50 hover:bg-white/10'
          }`}
      >
        {cta}
      </a>
    )}
  </div>
);

/* ─────────────────────────── TRUST ITEMS ───────────────────────────── */
const trustItems = [
  { icon: <Landmark className="w-6 h-6" />, label: 'Built on NIST FIPS 203 / 204 / 205 standards' },
  { icon: <Globe className="w-6 h-6" />, label: 'RapidAPI listed' },
  { icon: <Lock className="w-6 h-6" />, label: 'DPDPA compliant' },
  { icon: <Zap className="w-6 h-6" />, label: '99.7% uptime SLA' },
];

/* ═══════════════════════════════════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════════════════════════════════ */
export default function LandingPage() {
  usePageTracking('home');
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleProClick = () => {
    const wplusCheckoutUrl = import.meta.env.VITE_WARRIORPLUS_CHECKOUT_URL || 'https://warriorplus.com/as/o/466941';
    window.location.href = wplusCheckoutUrl;
  };

  const [scanDomain, setScanDomain] = useState('');
  const showResult = false;

  const handleScan = (e: React.FormEvent) => {
    e.preventDefault();
    if (scanDomain.trim()) {
      navigate(`/pqc-scanner?domain=${encodeURIComponent(scanDomain.trim())}`);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      <Navbar />

      {/* ═══════════════════════════════════════════════════════════════
          ORIGINAL HERO — "Quantum Visionaries" + Interactive States
          ═══════════════════════════════════════════════════════════════ */}
      <section className="pt-32 pb-20 px-6 relative z-10">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="animate-fade-in">
              {/* Logo Section */}
              <div className="mb-8">
                <LogoProcessor
                  originalSrc="/lovable-uploads/56a0d2c9-73da-4624-bfb1-2bb520c4a4e3.png"
                  alt="QuantCAI Logo"
                  className="h-40 mb-4 drop-shadow-2xl brightness-110 contrast-125 saturate-110 hover:scale-105 transition-all duration-300"
                  style={{
                    filter: 'drop-shadow(0 0 20px rgba(59, 130, 246, 0.5)) drop-shadow(0 0 40px rgba(139, 92, 246, 0.3)) brightness(1.1) contrast(1.25) saturate(1.1)',
                    mixBlendMode: 'screen' as const,
                  }}
                />
              </div>

              <h1 className="text-6xl md:text-7xl font-bold mb-6 leading-tight text-white drop-shadow-lg">
                Quantum Visionaries
              </h1>
              <h2 className="text-2xl md:text-3xl mb-5 font-light text-blue-100 drop-shadow-md">
                Leap Forward to Innovate, Educate, and Elevate <br />
                Tech Horizons
              </h2>
              <p className="text-lg mb-12 max-w-2xl leading-relaxed text-blue-200 drop-shadow-sm">
                QuantCAI is leading the quantum computer adaptation to the world through
                interactive education and cutting-edge simulations.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <Link to="/learn" className="w-full sm:w-auto">
                  <Button className="w-full bg-gradient-to-r from-blue-600 to-purple-700 hover:from-blue-700 hover:to-purple-800 text-white px-8 py-4 text-lg rounded-lg transform hover:scale-105 transition-all duration-300 flex items-center gap-2 shadow-2xl shadow-blue-500/30 border border-blue-400/30">
                    <Rocket className="h-5 w-5" />
                    Explore Quantum World
                  </Button>
                </Link>
                <Link to="/sandbox" className="w-full sm:w-auto">
                  <Button
                    variant="outline"
                    className="w-full border-2 border-blue-400 text-blue-200 hover:bg-blue-500/20 hover:text-white px-8 py-4 text-lg rounded-lg transform hover:scale-105 transition-all duration-300 flex items-center gap-2 backdrop-blur-sm bg-white/5 shadow-xl"
                  >
                    <Settings className="h-5 w-5" />
                    Try Simulator
                  </Button>
                </Link>
              </div>
            </div>

            {/* Interactive Quantum States Section */}
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-8 border border-blue-400/40 shadow-2xl shadow-blue-500/30">
              <h3 className="text-2xl font-bold text-white mb-4 drop-shadow-md">
                Interactive Quantum States
              </h3>
              <p className="text-blue-100 mb-6 drop-shadow-sm">
                Experience real-time quantum superposition and entanglement
              </p>
              <div className="relative">
                <div className="bg-gradient-to-br from-blue-500/30 to-purple-500/30 p-6 rounded-xl border border-blue-400/40 backdrop-blur-sm shadow-xl">
                  <div className="flex items-center justify-center h-32 relative">
                    <div className="relative">
                      <Atom className="h-16 w-16 text-blue-300 animate-pulse drop-shadow-lg" />
                      <div className="absolute -top-2 -right-2 w-4 h-4 bg-yellow-400 rounded-full animate-ping shadow-lg" />
                      <div className="absolute -bottom-2 -left-2 w-3 h-3 bg-green-400 rounded-full animate-bounce shadow-md" />
                      <div className="absolute top-0 left-0 w-2 h-2 bg-purple-400 rounded-full animate-pulse shadow-sm" />
                    </div>
                  </div>
                  <div className="text-center mt-4">
                    <p className="text-white font-semibold text-xl drop-shadow-md">
                      |ψ⟩ = α|0⟩ + β|1⟩
                    </p>
                    <p className="text-blue-200 text-sm mt-2 drop-shadow-sm">
                      Quantum Superposition State
                    </p>
                  </div>
                </div>
              </div>
              <Link to="/quantum-states">
                <Button className="w-full mt-6 bg-gradient-to-r from-blue-600 to-purple-700 hover:from-blue-700 hover:to-purple-800 text-white flex items-center justify-center gap-2 shadow-2xl shadow-blue-500/30 border border-blue-400/30">
                  Launch Interactive Quantum States
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          NEW: FEATURE SPLIT — API Terminal + PQC Scanner
          Glassmorphic cards · transparent over space background
          ═══════════════════════════════════════════════════════════════ */}
      <section id="features" className="py-20 sm:py-28 px-6 relative z-10">
        <div className="max-w-6xl mx-auto">
          {/* Section header */}
          <div className="text-center mb-16">
            <p className="text-qc-accent text-xs font-mono uppercase tracking-widest mb-3 drop-shadow-sm">
              Two APIs. One Platform.
            </p>
            <h2 className="font-bold text-2xl sm:text-3xl text-white drop-shadow-md">
              Built for developers. Trusted by security teams.
            </h2>
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            {/* ── LEFT: Quantum Simulation API ── */}
            <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-blue-400/20 shadow-2xl shadow-blue-500/10 hover:border-blue-400/40 hover:shadow-blue-500/20 transition-all duration-300 p-6 sm:p-8 group">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 rounded-lg border border-cyan-400/30 flex items-center justify-center text-qc-accent bg-cyan-500/10">
                  <Terminal className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-white drop-shadow-md">
                    Quantum Simulation API
                  </h3>
                  <p className="text-blue-200 text-xs">For developers</p>
                </div>
              </div>

              <p className="text-blue-200 text-sm mb-6 leading-relaxed drop-shadow-sm">
                POST your OpenQASM circuit. Get results back in &lt; 3 seconds.
                Statevector, counts, and noise-model simulation — all via REST.
              </p>

              {/* Code block — Request */}
              <div className="bg-black/40 backdrop-blur-sm rounded-xl border border-white/10 overflow-hidden mb-3">
                <div className="flex items-center gap-2 px-3 py-1.5 border-b border-white/10">
                  <span className="w-2 h-2 rounded-full bg-red-500/60" />
                  <span className="w-2 h-2 rounded-full bg-yellow-500/60" />
                  <span className="w-2 h-2 rounded-full bg-green-500/60" />
                  <span className="ml-2 text-[10px] text-blue-300 font-mono">request.sh</span>
                </div>
                <pre className="p-4 text-xs sm:text-[13px] leading-relaxed text-blue-100 font-mono overflow-x-auto">
                  <code>{curlSnippet}</code>
                </pre>
              </div>

              {/* Code block — Response */}
              <div className="bg-black/40 backdrop-blur-sm rounded-xl border border-white/10 overflow-hidden">
                <div className="flex items-center gap-2 px-3 py-1.5 border-b border-white/10">
                  <span className="text-[10px] text-qc-accent font-mono">← 200 OK</span>
                </div>
                <pre className="p-4 text-xs sm:text-[13px] leading-relaxed text-qc-accent/80 font-mono overflow-x-auto">
                  <code>{responseSnippet}</code>
                </pre>
              </div>
            </div>

            {/* ── RIGHT: PQC Scanner ── */}
            <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-blue-400/20 shadow-2xl shadow-blue-500/10 hover:border-blue-400/40 hover:shadow-blue-500/20 transition-all duration-300 p-6 sm:p-8 group">
              <Link to="/pqc-scanner" className="flex items-center gap-3 mb-4 cursor-pointer hover:opacity-85 transition-opacity">
                <div className="w-9 h-9 rounded-lg border border-cyan-400/30 flex items-center justify-center text-qc-accent bg-cyan-500/10">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-white drop-shadow-md hover:text-cyan-300 transition-colors">
                    PQC Vulnerability Scanner
                  </h3>
                  <p className="text-blue-200 text-xs">For security teams</p>
                </div>
              </Link>

              <p className="text-blue-200 text-sm mb-6 leading-relaxed drop-shadow-sm">
                Is your TLS stack quantum-safe? We'll tell you in 30 seconds.
                Full certificate-chain audit with NIST PQC compliance scoring.
              </p>

              {/* Scanner input */}
              <form onSubmit={handleScan} className="mb-6">
                <div className="flex gap-2">
                  <input
                    id="scanner-input"
                    type="text"
                    placeholder="Enter a domain to scan"
                    value={scanDomain}
                    onChange={(e) => setScanDomain(e.target.value)}
                    className="flex-1 px-3 py-2.5 rounded-lg border border-white/10 bg-black/30 backdrop-blur-sm text-white text-sm font-mono placeholder:text-blue-300/40 focus:outline-none focus:border-qc-accent/50 transition-colors"
                  />
                  <button
                    id="scanner-btn"
                    type="submit"
                    className="px-4 py-2.5 rounded-lg bg-qc-accent text-black text-sm font-semibold hover:brightness-110 transition-all whitespace-nowrap shadow-lg shadow-cyan-500/25"
                  >
                    Scan Now
                  </button>
                </div>
              </form>

              {/* Demo result card */}
              <div
                className={`rounded-xl border overflow-hidden transition-all duration-500 bg-black/30 backdrop-blur-sm ${showResult
                  ? 'border-red-500/40 opacity-100'
                  : 'border-white/10 opacity-60'
                  }`}
              >
                <div className="px-4 py-2.5 border-b border-white/10 flex items-center justify-between">
                  <span className="text-sm font-mono text-white">
                    {showResult && scanDomain ? scanDomain : 'example.com'}
                  </span>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-red-500/20 text-red-400 tracking-wider">
                    CRITICAL
                  </span>
                </div>
                <div className="p-4 space-y-3">
                  <div className="flex items-start gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm text-white font-mono">RSA-2048 certificate detected</p>
                      <p className="text-xs text-blue-300 mt-0.5">
                        Vulnerable to Shor's algorithm · Estimated break: 2030–2035
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm text-white font-mono">
                        ECDHE key exchange — not quantum-safe
                      </p>
                      <p className="text-xs text-blue-300 mt-0.5">
                        Migrate to ML-KEM (FIPS 203) for hybrid key exchange
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-yellow-500 mt-1.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm text-white font-mono">SHA-256 hashing — acceptable</p>
                      <p className="text-xs text-blue-300 mt-0.5">
                        Grover's provides only quadratic speedup · Low risk
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between">
                    <span className="text-xs text-blue-300 font-mono">Risk Score</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-1.5 rounded-full bg-white/10 overflow-hidden">
                        <div className="w-[85%] h-full rounded-full bg-red-500" />
                      </div>
                      <span className="text-sm font-mono font-bold text-red-400">8.5/10</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          NEW: PRICING — 3 tiers, anchored to Pro
          ═══════════════════════════════════════════════════════════════ */}
      <section id="pricing" className="py-20 sm:py-28 px-6 bg-white/[0.03] backdrop-blur-sm relative z-10">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <p className="text-qc-accent text-xs font-mono uppercase tracking-widest mb-3 drop-shadow-sm">
              Pricing
            </p>
            <h2 className="font-bold text-2xl sm:text-3xl text-white mb-3 drop-shadow-md">
              Start free. Scale when you're ready.
            </h2>
            <p className="text-blue-200 text-sm max-w-lg mx-auto drop-shadow-sm">
              No credit card required for Free tier. All plans include API access to both
              quantum simulation and PQC scanning.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <PlanCard
              name="Free"
              price="₹0"
              features={[
                'Basic access to Learning Hub',
                'Standard single-qubit simulations',
                '20 API calls / day',
                'Max 1,024 shots',
                '3 PQC domain scans / mo',
                'Ideal noise simulator only',
                'Community support',
              ]}
              cta="Start Free"
              ctaHref="/signup"
            />
            <PlanCard
              name="Pro"
              price="₹2,400"
              period="month"
              badge="Most Popular"
              highlighted
              features={[
                '500 API calls / day',
                'Max 65,536 shots + noise models',
                '50 PQC domain scans / mo',
                'Thermal & Depolarizing noise',
                'AI Tutor access (QuantAI)',
                'Standard static PDF CBOM export',
                'Priority email support',
              ]}
              cta="Upgrade to Pro"
              onClick={handleProClick}
              loading={false}
            />
            <PlanCard
              name="Enterprise"
              price="₹24,999"
              period="month"
              features={[
                'Sovereign PQC compliance suite',
                'CycloneDX 1.6 automated CBOM generation',
                'Internal network & port scanning',
                'LQM remediation & vulnerability mapping',
                'SSO + multi-user organization console',
                'Dedicated SLA & consultative procurement',
              ]}
              cta="Contact Sales"
              ctaHref="mailto:sales@quantcai.in"
            />
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          NEW: TRUST BADGES
          ═══════════════════════════════════════════════════════════════ */}
      <section id="trust" className="py-16 sm:py-20 px-6 relative z-10 border-t border-blue-500/10">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 sm:gap-8">
            {trustItems.map((item, i) => (
              <div
                key={i}
                className="flex flex-col items-center text-center gap-3 p-4 rounded-xl border border-transparent hover:border-blue-400/20 hover:bg-white/5 transition-all duration-200"
              >
                <div className="text-qc-accent drop-shadow-lg">{item.icon}</div>
                <p className="text-blue-200 text-xs sm:text-sm leading-snug drop-shadow-sm">
                  {item.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          NEW: CTA BANNER — "The quantum advantage starts now."
          ═══════════════════════════════════════════════════════════════ */}
      <section className="py-20 sm:py-28 px-6 relative z-10">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="font-bold text-2xl sm:text-3xl text-white mb-4 drop-shadow-lg">
            The quantum advantage starts now.
          </h2>
          <p className="text-blue-200 text-sm sm:text-base max-w-xl mx-auto mb-8 leading-relaxed drop-shadow-sm">
            Whether you're building quantum algorithms or hardening your infrastructure
            against quantum threats — QuantCAI gives you the tools to move first.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <a
              href="/signup"
              className="w-full sm:w-auto px-6 py-3 rounded-lg bg-qc-accent text-black font-semibold text-sm hover:brightness-110 transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/25"
            >
              Get Started Free
              <ArrowRight className="w-4 h-4" />
            </a>
            <a
              href="/docs"
              className="w-full sm:w-auto px-6 py-3 rounded-lg border border-blue-400/30 text-white font-medium text-sm hover:border-blue-400/50 hover:bg-white/10 transition-all duration-200"
            >
              Read the Docs
            </a>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          ORIGINAL: NEWSLETTER
          ═══════════════════════════════════════════════════════════════ */}
      <section className="py-20 px-6 bg-white/5 backdrop-blur-sm relative z-10">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-6 drop-shadow-lg">
            Stay Updated with Quantum Innovations
          </h2>
          <p className="text-xl text-blue-200 mb-8 drop-shadow-md">
            Get the latest insights on quantum computing, research breakthroughs, and
            educational content.
          </p>
          <NewsletterForm />
        </div>
      </section>

      <Footer />
    </div>
  );
}
