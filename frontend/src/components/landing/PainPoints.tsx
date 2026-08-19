import { ShieldAlert, CalendarClock, FileSearch, GitCompareArrows } from 'lucide-react';

/**
 * The problem statement.
 *
 * Every claim here is checkable against a primary source, and the dates are
 * the ones that actually apply to TLS endpoints. Vendor marketing routinely
 * quotes CNSA 2.0's 2030 date at web servers; 2030 is the software and
 * firmware signing deadline, and quoting it at the wrong system class is the
 * fastest way to lose credibility with the security buyer reading this page.
 */
const problems = [
  {
    icon: ShieldAlert,
    tone: 'danger' as const,
    title: 'Traffic captured today is decrypted later',
    body:
      'Encrypted sessions are being recorded now and stored until a quantum computer can break the key exchange that protected them. Anything with a confidentiality lifetime measured in years — health records, contracts, source code, keys — is already exposed, whatever your current TLS grade says.',
    tag: 'Harvest now, decrypt later',
  },
  {
    icon: CalendarClock,
    tone: 'warn' as const,
    title: 'The compliance dates are already in force',
    body:
      'CNSA 2.0 requires web servers, browsers and cloud services to prefer post-quantum algorithms from 2025 and use them exclusively by 2033. Separately, FIPS 140-2 certificates move to historical status in September 2026, which closes the door for new federal procurement.',
    tag: 'CNSA 2.0 · FIPS 140-3',
  },
  {
    icon: FileSearch,
    tone: 'danger' as const,
    title: 'Nobody can list the cryptography they run',
    body:
      'Migration planning stalls at the first question: which endpoints, certificates, libraries and key exchanges are actually in use? Without a machine-readable inventory, the answer is a spreadsheet that is out of date the day it is finished.',
    tag: 'No CBOM',
  },
  {
    icon: GitCompareArrows,
    tone: 'warn' as const,
    title: 'A CDN-green result hides the origin',
    body:
      'Most observed post-quantum TLS deployment sits at a handful of CDNs. A scan of your public hostname measures the edge — the leg from that edge to your origin can still be legacy TLS with classical key exchange, and it is the leg your auditor will ask about.',
    tag: 'Edge vs origin',
  },
];

const toneStyles = {
  danger: {
    icon: 'text-qc-danger',
    ring: 'bg-qc-danger/10 border-qc-danger/25',
    pill: 'qc-pill-danger',
  },
  warn: {
    icon: 'text-qc-warn',
    ring: 'bg-qc-warn/10 border-qc-warn/25',
    pill: 'qc-pill-warn',
  },
};

export const PainPoints = () => (
  <section id="problem" className="qc-section border-t border-qc-border">
    <div className="qc-container">
      <div className="max-w-3xl">
        <span className="qc-eyebrow">The problem</span>
        <h2 className="text-fluid-h2 font-bold text-qc-text mt-3">
          Your TLS is fine today. That is the problem.
        </h2>
        <p className="text-fluid-lead text-qc-muted mt-4 qc-measure">
          Post-quantum migration is not a future project with a future deadline. The
          exposure starts the moment traffic is recorded, and the inventory work that
          has to happen first takes longer than the migration itself.
        </p>
      </div>

      <div className="grid gap-4 sm:gap-5 md:grid-cols-2 mt-10 md:mt-14">
        {problems.map(({ icon: Icon, tone, title, body, tag }) => {
          const styles = toneStyles[tone];
          return (
            <article
              key={title}
              className="qc-card qc-card-interactive p-5 sm:p-7 flex flex-col"
            >
              <div className="flex items-start gap-4">
                <span
                  className={`shrink-0 grid place-items-center w-11 h-11 rounded-lg border ${styles.ring}`}
                  aria-hidden="true"
                >
                  <Icon className={`w-5 h-5 ${styles.icon}`} />
                </span>
                <div className="min-w-0">
                  <h3 className="text-lg sm:text-xl font-semibold text-qc-text leading-snug">
                    {title}
                  </h3>
                  <span className={`qc-pill ${styles.pill} mt-2`}>{tag}</span>
                </div>
              </div>
              <p className="text-sm sm:text-[0.9375rem] leading-relaxed text-qc-muted mt-4">
                {body}
              </p>
            </article>
          );
        })}
      </div>
    </div>
  </section>
);
