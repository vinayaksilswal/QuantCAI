import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Shield, Lock, Eye, CheckCircle, Server, FileText, ArrowRight } from 'lucide-react';
import { usePageTracking } from '@/hooks/usePageTracking';

const Security = () => {
  usePageTracking('security');

  return (
    <div className="min-h-screen relative">
      <Navbar />

      <div className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
              Security &{' '}
              <span className="bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
                Compliance
              </span>
            </h1>
            <p className="text-xl text-gray-300 leading-relaxed">
              Documenting our post-quantum security architecture, data handling, and regulatory compliance.
            </p>
          </div>

          {/* Main Content */}
          <div className="bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm rounded-xl p-8 md:p-12 space-y-12">
            
            {/* Overview */}
            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400 border border-emerald-500/25">
                  <Shield className="w-6 h-6" />
                </div>
                <h2 className="text-2xl font-bold text-white">Quantum-Safe Posture</h2>
              </div>
              <p className="text-gray-300 leading-relaxed">
                QuantCAI is built from the ground up to prepare modern digital infrastructures for the quantum era. 
                We actively track and implement guidelines aligned with NIST's Post-Quantum Cryptography (PQC) standards 
                and the Commercial National Security Algorithm Suite (CNSA 2.0). 
              </p>
            </section>

            {/* Core Commitments */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="p-6 rounded-xl bg-slate-900/40 border border-slate-800 space-y-3">
                <div className="text-emerald-400 font-bold flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" />
                  NIST FIPS Alignment
                </div>
                <p className="text-xs text-gray-400 leading-relaxed">
                  Our cryptographic analysis maps configurations to FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), and FIPS 205 (SLH-DSA) to guarantee forward-looking migration strategies.
                </p>
              </div>

              <div className="p-6 rounded-xl bg-slate-900/40 border border-slate-800 space-y-3">
                <div className="text-emerald-400 font-bold flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" />
                  Hybrid TLS Readiness
                </div>
                <p className="text-xs text-gray-400 leading-relaxed">
                  We audit target domains for hybrid post-quantum key exchange algorithms (e.g., X25519MLKEM768) ensuring compliance with CNSA 2.0 timelines.
                </p>
              </div>
            </div>

            {/* Encryption and Infrastructure */}
            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400 border border-blue-500/25">
                  <Lock className="w-6 h-6" />
                </div>
                <h2 className="text-2xl font-bold text-white">Data Protection & Encryption</h2>
              </div>
              <ul className="space-y-3 text-gray-300">
                <li className="flex items-start gap-2.5">
                  <span className="text-emerald-400 mr-1 mt-1 font-bold">•</span>
                  <span><strong>Data in Transit:</strong> All communications between users, API clients, and the QuantCAI platform are encrypted using TLS 1.3 or high-grade TLS 1.2 with strong ephemeral key exchanges.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-emerald-400 mr-1 mt-1 font-bold">•</span>
                  <span><strong>Data at Rest:</strong> Core transaction databases, billing details, and audit records are encrypted at rest using AES-256 with managed key rotation.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-emerald-400 mr-1 mt-1 font-bold">•</span>
                  <span><strong>API Key Security:</strong> Developer API keys are stored as cryptographically hashed SHA-256 signatures. The plaintext API key is only shown once at creation and is never stored in readable format.</span>
                </li>
              </ul>
            </section>

            {/* Access Controls */}
            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400 border border-purple-500/25">
                  <Server className="w-6 h-6" />
                </div>
                <h2 className="text-2xl font-bold text-white">Role-Based Access Control (RBAC)</h2>
              </div>
              <p className="text-gray-300 leading-relaxed">
                QuantCAI accounts enforce strict separation of duties through built-in workspace roles. 
                Permissions are limited to the minimum set required for each organizational profile:
              </p>
              <div className="grid sm:grid-cols-3 gap-4 text-xs font-mono text-gray-400 mt-2">
                <div className="border border-slate-700/50 p-4 rounded bg-slate-900/20">
                  <span className="text-white font-bold block mb-1">Security Analyst</span>
                  Initiates and analyzes public and internal PQC scans, generates CBOM compliance reports.
                </div>
                <div className="border border-slate-700/50 p-4 rounded bg-slate-900/20">
                  <span className="text-white font-bold block mb-1">Developer</span>
                  Accesses quantum simulators, builds circuit templates, provisions API credentials.
                </div>
                <div className="border border-slate-700/50 p-4 rounded bg-slate-900/20">
                  <span className="text-white font-bold block mb-1">Administrator</span>
                  Manages team onboarding, billing details, custom domain integrations, and RLS policies.
                </div>
              </div>
            </section>

            {/* PQC Scanning Safety */}
            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-cyan-500/10 rounded-lg text-cyan-400 border border-cyan-500/25">
                  <Eye className="w-6 h-6" />
                </div>
                <h2 className="text-2xl font-bold text-white">Safe Scanning & SSRF Prevention</h2>
              </div>
              <p className="text-gray-300 leading-relaxed">
                Our cryptographic scanning engine implements custom IP blocklists and strict hostname resolution steps. 
                This design prevents Server-Side Request Forgery (SSRF) and blocks access to sensitive internal networks 
                unless authenticated enterprise subnets are explicitly configured. Audit activities are conducted safely 
                and non-intrusively without active exploit testing.
              </p>
            </section>

            {/* Reporting */}
            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-red-500/10 rounded-lg text-red-400 border border-red-500/25">
                  <FileText className="w-6 h-6" />
                </div>
                <h2 className="text-2xl font-bold text-white">Reporting Vulnerabilities</h2>
              </div>
              <p className="text-gray-300 leading-relaxed">
                If you believe you have discovered a security vulnerability in the QuantCAI platform, please contact us 
                immediately. We operate a coordinated disclosure process to address concerns promptly.
              </p>
              <div className="pt-2">
                <a
                  href="mailto:support@quantcai.in?subject=Coordinated%20Vulnerability%20Disclosure"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-emerald-500 text-slate-950 font-bold hover:bg-emerald-400 transition-colors text-sm"
                >
                  Report a Security Finding
                  <ArrowRight className="w-4 h-4" />
                </a>
              </div>
            </section>

            {/* Footer metadata */}
            <div className="border-t border-slate-700/50 pt-6 mt-8">
              <p className="text-gray-500 text-sm text-center">
                Detailed RFC 9116 security policies can be found at <a href="/.well-known/security.txt" className="text-blue-400 hover:underline">quantcai.in/.well-known/security.txt</a>
              </p>
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default Security;
