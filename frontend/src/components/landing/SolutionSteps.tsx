import { Link } from 'react-router-dom';
import { Radar, FileJson, BellRing, TerminalSquare, ArrowRight } from 'lucide-react';

/**
 * The answer to each problem, in the order a customer actually does the work.
 *
 * Every capability listed here ships today. Nothing on this page describes
 * roadmap work — a security buyer who signs up and cannot find an advertised
 * feature does not come back, and the trust cost far outweighs the extra
 * bullet point.
 */
const steps = [
  {
    icon: Radar,
    step: '01',
    title: 'Discover what you are running',
    body:
      'Point the scanner at a domain and get the negotiated TLS version, key exchange group, cipher and full certificate chain, each graded against NIST FIPS 203/204/205. Results flag when a session terminates at a CDN, so an edge-green result is never mistaken for origin readiness.',
    cta: { label: 'Scan a domain', to: '/pqc-scanner' },
  },
  {
    icon: FileJson,
    step: '02',
    title: 'Export an inventory your auditor accepts',
    body:
      'Generate a CycloneDX 1.6 Cryptographic Bill of Materials as a signed-off artifact — algorithms, key sizes, certificates and their relationships in a machine-readable file that drops into GRC tooling and CI pipelines instead of a spreadsheet.',
    cta: { label: 'See CBOM output', to: '/pqc-scanner' },
    badge: 'Pro',
  },
  {
    icon: BellRing,
    step: '03',
    title: 'Watch it continuously',
    body:
      'Register the domains that matter and have them rescanned on a schedule, so a certificate rotation or load-balancer change that reintroduces a classical key exchange surfaces as a finding rather than an audit surprise. Publish a public readiness badge when you are ready to show the work.',
    cta: { label: 'View enterprise plan', to: '/enterprise' },
    badge: 'Enterprise',
  },
  {
    icon: TerminalSquare,
    step: '04',
    title: 'Wire it into your own systems',
    body:
      'A REST API with scoped keys, per-key rate limits and usage metering, plus a quantum circuit simulator with OpenQASM 3 export for the research side of the house. Bring your own IBM Quantum or IonQ credentials to run against real hardware.',
    cta: { label: 'Open the developer console', to: '/profile' },
  },
];

export const SolutionSteps = () => (
  <section id="solution" className="qc-section border-t border-qc-border bg-qc-bg-raised">
    <div className="qc-container">
      <div className="max-w-3xl">
        <span className="qc-eyebrow">The work</span>
        <h2 className="text-fluid-h2 font-bold text-qc-text mt-3">
          Inventory first, then migrate.
        </h2>
        <p className="text-fluid-lead text-qc-muted mt-4 qc-measure">
          You cannot migrate cryptography you have not catalogued. QuantCAI covers the
          discovery and evidence half of the problem, which is the half that blocks
          everything else.
        </p>
      </div>

      <ol className="mt-10 md:mt-14 grid gap-4 sm:gap-5 lg:grid-cols-2">
        {steps.map(({ icon: Icon, step, title, body, cta, badge }) => (
          <li key={step} className="qc-card qc-card-interactive p-5 sm:p-7 flex flex-col">
            <div className="flex items-center gap-3">
              <span
                className="grid place-items-center w-10 h-10 rounded-lg bg-qc-accent-dim border border-qc-accent/25"
                aria-hidden="true"
              >
                <Icon className="w-5 h-5 text-qc-accent" />
              </span>
              <span className="font-mono text-xs text-qc-subtle tracking-widest">
                {step}
              </span>
              {badge && (
                <span className="qc-pill qc-pill-neutral ml-auto">{badge}</span>
              )}
            </div>

            <h3 className="text-lg sm:text-xl font-semibold text-qc-text mt-4 leading-snug">
              {title}
            </h3>
            <p className="text-sm sm:text-[0.9375rem] leading-relaxed text-qc-muted mt-3 flex-1">
              {body}
            </p>

            <Link
              to={cta.to}
              className="qc-tap inline-flex items-center gap-2 text-sm font-semibold text-qc-accent hover:text-qc-accent-hover mt-5 group"
            >
              {cta.label}
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </li>
        ))}
      </ol>
    </div>
  </section>
);
