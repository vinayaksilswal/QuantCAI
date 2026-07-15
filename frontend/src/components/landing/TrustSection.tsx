/* ── Inline SVG Icons ─────────────────────────────────────────────── */
const NistIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0 0 12 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75Z" />
  </svg>
);

const GlobeIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 0 1 7.843 4.582M12 3a8.997 8.997 0 0 0-7.843 4.582m15.686 0A11.953 11.953 0 0 1 12 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0 1 21 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0 1 12 16.5a17.92 17.92 0 0 1-8.716-2.247m0 0A9.015 9.015 0 0 1 3 12c0-1.605.42-3.113 1.157-4.418" />
  </svg>
);

const LockIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
  </svg>
);

const BoltIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
  </svg>
);

const ShieldCheckIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
  </svg>
);

const CodeIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
  </svg>
);

const trustItems = [
  { icon: <NistIcon />, label: 'Built on NIST FIPS 203 / 204 / 205 standards', metric: '3 NIST Standards' },
  { icon: <GlobeIcon />, label: 'RapidAPI listed — global API marketplace', metric: 'Listed on RapidAPI' },
  { icon: <LockIcon />, label: 'DPDPA compliant data handling', metric: 'Privacy Compliant' },
  { icon: <BoltIcon />, label: '99.7% uptime SLA guarantee', metric: '99.7% Uptime' },
  { icon: <ShieldCheckIcon />, label: '10,000+ domains scanned for quantum vulnerabilities', metric: '10K+ Scans' },
  { icon: <CodeIcon />, label: '500+ developers trust our quantum simulation API', metric: '500+ Developers' },
];

export const TrustSection = () => (
  <section id="trust" className="py-16 sm:py-24 px-4 sm:px-6 relative z-10">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <p className="text-teal-400 text-xs font-mono uppercase tracking-widest mb-3 drop-shadow-sm">Why Teams Trust QuantCAI</p>
        <h2 className="text-3xl sm:text-4xl font-bold text-white drop-shadow-lg">
          Enterprise-grade security infrastructure
        </h2>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-5 sm:gap-6">
        {trustItems.map((item, i) => (
          <div
            key={i}
            className="flex flex-col items-center text-center gap-3 p-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl hover:border-teal-400/30 hover:bg-white/[0.08] transition-all duration-300 shadow-lg shadow-blue-500/5 group"
          >
            <div className="text-teal-400 drop-shadow-lg group-hover:scale-110 transition-transform duration-300">{item.icon}</div>
            <p className="text-white text-sm font-semibold drop-shadow-md">{item.metric}</p>
            <p className="text-blue-300/70 text-xs leading-snug">{item.label}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);
