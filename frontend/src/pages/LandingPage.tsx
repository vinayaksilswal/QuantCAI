import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { usePageTracking } from '@/hooks/usePageTracking';
import {
  ShieldCheck, ArrowRight, Search, Check, FileJson, Landmark, Lock, Terminal,
} from 'lucide-react';
import { Navbar } from '@/components/Navbar';
import { PainPoints } from '@/components/landing/PainPoints';
import { SolutionSteps } from '@/components/landing/SolutionSteps';
import { PricingSection } from '@/components/landing/PricingSection';
import { Footer } from '@/components/Footer';
import { SEO } from '@/components/SEO';

/* ────────────────────────────── API SAMPLE ──────────────────────────────
   Uses the branded API host rather than the raw platform hostname. An
   onrender.com URL in a public code sample tells an enterprise evaluator the
   backend is a hobby deployment, whatever the product actually does.        */
const curlSnippet = `curl -X POST https://backend.quantcai.in/api/v1/pqc/scan \\
  -H "X-API-Key: qc_live_your_key" \\
  -H "Content-Type: application/json" \\
  -d '{"domain": "example.com"}'`;

const responseSnippet = `{
  "domain": "example.com",
  "risk_level": "HIGH",
  "tls_version": "TLSv1.3",
  "key_exchange": "x25519",
  "key_exchange_risk": "VULNERABLE",
  "scan_scope": "edge",
  "cnsa_2_0": { "prefer_by": 2025, "exclusive_use_by": 2033 }
}`;

/* Standards the product is actually built against. Kept factual and
   verifiable — no uptime or certification claims that cannot be evidenced. */
const standards = [
  { icon: Landmark, label: 'NIST FIPS 203 / 204 / 205' },
  { icon: ShieldCheck, label: 'NSA CNSA 2.0 timeline' },
  { icon: FileJson, label: 'CycloneDX 1.6 CBOM' },
  { icon: Lock, label: 'OWASP crypto-asset schema' },
];

const LandingPage = () => {
  usePageTracking('home');
  const navigate = useNavigate();
  const [domain, setDomain] = useState('');

  const handleScan = (e: React.FormEvent) => {
    e.preventDefault();
    const cleaned = domain
      .trim()
      .replace(/^https?:\/\//i, '')
      .replace(/\/.*$/, '');
    if (!cleaned) return;
    navigate(`/pqc-scanner?domain=${encodeURIComponent(cleaned)}`);
  };

  return (
    <div className="min-h-dvh bg-qc-bg">
      <SEO
        title="QuantCAI — Post-Quantum Readiness for TLS"
        description="Scan your endpoints against NIST FIPS 203/204/205, export a CycloneDX CBOM, and evidence your post-quantum migration before the CNSA 2.0 deadlines."
      />
      <Navbar />

      {/* ─────────────────────────────── HERO ─────────────────────────────── */}
      <header className="relative overflow-hidden">
        <div className="absolute inset-0 qc-grid-bg pointer-events-none" aria-hidden="true" />

        <div className="qc-container relative pt-28 sm:pt-32 pb-16 sm:pb-24">
          <div className="grid lg:grid-cols-12 gap-10 lg:gap-14 items-start">
            <div className="lg:col-span-7 animate-fade-in">
              <span className="qc-eyebrow">
                <span className="w-1.5 h-1.5 rounded-full bg-qc-accent" aria-hidden="true" />
                Post-quantum readiness for TLS
              </span>

              <h1 className="text-fluid-display font-bold text-qc-text mt-4">
                The traffic you encrypt today is
                <span className="text-qc-danger"> already being collected.</span>
              </h1>

              <p className="text-fluid-lead text-qc-muted mt-5 qc-measure">
                Recorded sessions get decrypted the day a quantum computer can break
                today&apos;s key exchange. QuantCAI shows you which of your endpoints are
                exposed, gives you the cryptographic inventory your auditor asks for,
                and tracks it until the migration is done.
              </p>

              {/* Primary conversion path: a domain, not a signup form. */}
              <form onSubmit={handleScan} className="mt-8 max-w-xl">
                <label htmlFor="scan-domain" className="sr-only">
                  Domain to scan
                </label>
                <div className="flex flex-col sm:flex-row gap-3">
                  <div className="relative flex-1">
                    <Search
                      className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-qc-subtle pointer-events-none"
                      aria-hidden="true"
                    />
                    <input
                      id="scan-domain"
                      type="text"
                      inputMode="url"
                      autoComplete="url"
                      autoCapitalize="none"
                      spellCheck={false}
                      value={domain}
                      onChange={(e) => setDomain(e.target.value)}
                      placeholder="yourcompany.com"
                      className="qc-tap w-full rounded-lg border border-qc-border-strong bg-qc-surface pl-10 pr-4 py-3 text-base text-qc-text placeholder:text-qc-subtle focus:border-qc-accent focus:outline-none focus:ring-2 focus:ring-qc-accent/30"
                    />
                  </div>
                  <button
                    type="submit"
                    className="qc-tap inline-flex items-center justify-center gap-2 rounded-lg bg-qc-accent px-6 py-3 text-base font-semibold text-qc-accent-fg transition-colors hover:bg-qc-accent-hover disabled:opacity-50"
                  >
                    Check readiness
                    <ArrowRight className="w-4 h-4" aria-hidden="true" />
                  </button>
                </div>
                <p className="text-xs text-qc-subtle mt-2.5">
                  Free scan. A free account is required to view the full certificate
                  chain and findings.
                </p>
              </form>

              <div className="flex flex-wrap items-center gap-x-5 gap-y-2 mt-7">
                <Link
                  to="/circuit-builder"
                  className="qc-tap inline-flex items-center gap-2 text-sm font-medium text-qc-muted hover:text-qc-text"
                >
                  <Terminal className="w-4 h-4" aria-hidden="true" />
                  Building on quantum? Start in the simulator
                </Link>
              </div>
            </div>

            {/* Sample finding. Shows the product's actual output rather than an
                abstract illustration — the fastest way to communicate what this
                thing does. */}
            <div className="lg:col-span-5 w-full">
              <div className="qc-card shadow-qc-lg overflow-hidden">
                <div className="flex items-center justify-between gap-3 px-4 sm:px-5 py-3 border-b border-qc-border bg-qc-bg-raised">
                  <span className="font-mono text-xs text-qc-muted truncate">
                    GET /api/v1/scan/example.com
                  </span>
                  <span className="qc-pill qc-pill-danger shrink-0">Risk: High</span>
                </div>

                <dl className="divide-y divide-qc-border">
                  {[
                    { k: 'TLS version', v: 'TLS 1.3', tone: 'ok' },
                    { k: 'Key exchange', v: 'x25519', tone: 'danger' },
                    { k: 'Certificate', v: 'RSA-2048', tone: 'danger' },
                    { k: 'Symmetric', v: 'AES-256-GCM', tone: 'ok' },
                    { k: 'Scan scope', v: 'Edge (CDN)', tone: 'warn' },
                  ].map(({ k, v, tone }) => (
                    <div
                      key={k}
                      className="flex items-center justify-between gap-3 px-4 sm:px-5 py-3"
                    >
                      <dt className="text-sm text-qc-muted">{k}</dt>
                      <dd
                        className={`font-mono text-sm ${
                          tone === 'danger'
                            ? 'text-qc-danger'
                            : tone === 'warn'
                            ? 'text-qc-warn'
                            : 'text-qc-ok'
                        }`}
                      >
                        {v}
                      </dd>
                    </div>
                  ))}
                </dl>

                <div className="px-4 sm:px-5 py-4 border-t border-qc-border bg-qc-bg-raised">
                  <p className="text-xs leading-relaxed text-qc-muted">
                    <span className="text-qc-danger font-semibold">Finding.</span>{' '}
                    Classical key exchange is broken by Shor&apos;s algorithm. Deploy an
                    ML-KEM-768 hybrid group (FIPS&nbsp;203).
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Standards strip */}
          <div className="mt-14 sm:mt-20 pt-8 border-t border-qc-border">
            <p className="text-xs font-semibold uppercase tracking-widest text-qc-subtle">
              Assessed against
            </p>
            <ul className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mt-4">
              {standards.map(({ icon: Icon, label }) => (
                <li key={label} className="flex items-center gap-2.5 min-w-0">
                  <Icon className="w-4 h-4 text-qc-accent shrink-0" aria-hidden="true" />
                  <span className="text-sm text-qc-muted truncate">{label}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </header>

      <PainPoints />
      <SolutionSteps />

      {/* ───────────────────────────── DEVELOPER ───────────────────────────── */}
      <section className="qc-section border-t border-qc-border">
        <div className="qc-container">
          <div className="grid lg:grid-cols-2 gap-10 lg:gap-14 items-center">
            <div>
              <span className="qc-eyebrow">For engineers</span>
              <h2 className="text-fluid-h2 font-bold text-qc-text mt-3">
                One endpoint. Machine-readable answers.
              </h2>
              <p className="text-fluid-lead text-qc-muted mt-4 qc-measure">
                Wire readiness checks into CI so a deploy that reintroduces a classical
                key exchange fails the build instead of the audit. Scoped API keys,
                per-key rate limits, and usage you can see.
              </p>
              <ul className="mt-6 space-y-3">
                {[
                  'Scan and CBOM export from a single REST call',
                  'Tri-state results — never reports "unmeasured" as "vulnerable"',
                  'OpenQASM 3 circuit simulation on the same key',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5">
                    <Check className="w-4 h-4 text-qc-accent shrink-0 mt-1" aria-hidden="true" />
                    <span className="text-sm sm:text-[0.9375rem] text-qc-muted">{item}</span>
                  </li>
                ))}
              </ul>
              <Link
                to="/profile"
                className="qc-tap inline-flex items-center gap-2 mt-7 text-sm font-semibold text-qc-accent hover:text-qc-accent-hover group"
              >
                Get an API key
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </div>

            {/* Code panes scroll inside themselves; on a phone a wide <pre>
                would otherwise drag the whole page sideways. */}
            <div className="space-y-3 min-w-0">
              <div className="qc-card overflow-hidden">
                <div className="px-4 py-2.5 border-b border-qc-border bg-qc-bg-raised">
                  <span className="font-mono text-xs text-qc-subtle">Request</span>
                </div>
                <pre className="p-4 overflow-x-auto text-xs leading-relaxed text-qc-muted">
                  <code>{curlSnippet}</code>
                </pre>
              </div>
              <div className="qc-card overflow-hidden">
                <div className="px-4 py-2.5 border-b border-qc-border bg-qc-bg-raised">
                  <span className="font-mono text-xs text-qc-subtle">Response</span>
                </div>
                <pre className="p-4 overflow-x-auto text-xs leading-relaxed text-qc-muted">
                  <code>{responseSnippet}</code>
                </pre>
              </div>
            </div>
          </div>
        </div>
      </section>

      <PricingSection />

      {/* ─────────────────────────────── CTA ─────────────────────────────── */}
      <section className="qc-section border-t border-qc-border">
        <div className="qc-container">
          <div className="qc-card p-7 sm:p-12 text-center">
            <h2 className="text-fluid-h2 font-bold text-qc-text">
              Find out where you stand.
            </h2>
            <p className="text-fluid-lead text-qc-muted mt-4 mx-auto qc-measure-narrow">
              One scan tells you whether your endpoints negotiate a post-quantum key
              exchange today, and what it takes if they do not.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center mt-8">
              <Link
                to="/pqc-scanner"
                className="qc-tap inline-flex items-center justify-center gap-2 rounded-lg bg-qc-accent px-7 py-3 text-base font-semibold text-qc-accent-fg transition-colors hover:bg-qc-accent-hover"
              >
                <ShieldCheck className="w-4 h-4" aria-hidden="true" />
                Scan your domain
              </Link>
              <Link
                to="/enterprise"
                className="qc-tap inline-flex items-center justify-center gap-2 rounded-lg border border-qc-border-strong px-7 py-3 text-base font-semibold text-qc-text transition-colors hover:bg-qc-surface-hover"
              >
                Talk to us about enterprise
              </Link>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default LandingPage;
