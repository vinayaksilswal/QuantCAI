import { usePageTracking } from '@/hooks/usePageTracking';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Shield, Zap, Network, Fingerprint, Mail, ArrowRight, Server, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Enterprise() {
  usePageTracking('enterprise');

  return (
    <div className="min-h-screen relative overflow-hidden bg-slate-950 text-white">
      {/* Visual background elements */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 via-transparent to-emerald-500/5 pointer-events-none" />
      <div className="absolute top-1/4 right-1/4 w-[600px] h-[400px] bg-emerald-500/[0.03] rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/4 w-[500px] h-[300px] bg-blue-500/[0.03] rounded-full blur-[100px] pointer-events-none" />

      <Navbar />

      {/* Hero Section */}
      <section className="pt-20 pb-8 md:pt-28 md:pb-12 px-6 relative z-10">
        <div className="max-w-6xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-mono font-bold uppercase tracking-wider mb-3 animate-pulse">
            <Shield className="h-4 w-4" /> Enterprise Compliance Suite
          </div>

          <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-4 font-syne max-w-4xl mx-auto leading-[1.15]">
            Sovereign Post-Quantum <br />
            <span className="bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-500 bg-clip-text text-transparent drop-shadow-sm">
              Cryptographic Resilience
            </span>
          </h1>

          <p className="text-lg md:text-xl text-slate-300 max-w-2xl mx-auto mb-6 leading-relaxed font-light">
            Assess, map, and remediate legacy cryptographic dependencies across your organization's internal infrastructure before the Cryptanalytically Relevant Quantum Computer (CRQC) threat arrives.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="mailto:quantc.info@gmail.com?subject=QuantCAI%20Enterprise%20PQC%20Compliance%20Request"
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-slate-950 font-bold text-base flex items-center justify-center gap-2 shadow-2xl shadow-emerald-500/20 border border-emerald-400/30 transform hover:scale-105 transition-all duration-300"
            >
              Request Custom Demo
              <ArrowRight className="h-5 w-5" />
            </a>
            <Link to="/signup?plan=enterprise" className="w-full sm:w-auto">
              <Button variant="outline" className="w-full border-2 border-slate-700 hover:bg-slate-800/50 hover:border-slate-500 text-slate-300 px-8 py-4 text-base rounded-xl backdrop-blur-sm bg-white/5 transition-all duration-300">
                Register Organization
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Grid Section */}
      <section className="py-20 px-6 relative z-10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold font-syne mb-4">Core Commercial Capabilities</h2>
            <p className="text-slate-400 max-w-xl mx-auto">Enterprise-grade scanning and cryptographic configuration audits built for strict FIPS regulatory deadlines.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <Card className="bg-slate-900/60 border-slate-800/80 backdrop-blur-xl hover:border-emerald-500/30 transition-all duration-300 shadow-xl shadow-slate-950/50">
              <CardContent className="p-8">
                <div className="p-3 w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-6">
                  <Zap className="h-6 w-6" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">CycloneDX 1.6 Automated CBOM</h3>
                <p className="text-slate-300 leading-relaxed text-sm">
                  Generate machine-readable Cryptographic Bill of Materials (CBOM) directly mapped to CycloneDX 1.6 specifications. Auto-discover active protocols, public keys, curves, and hash algorithms to dynamically construct complete cryptographic catalogs.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-900/60 border-slate-800/80 backdrop-blur-xl hover:border-emerald-500/30 transition-all duration-300 shadow-xl shadow-slate-950/50">
              <CardContent className="p-8">
                <div className="p-3 w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-6">
                  <Network className="h-6 w-6" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">Internal Network & Port Scanning</h3>
                <p className="text-slate-300 leading-relaxed text-sm">
                  Run targeted audits on internal endpoints (such as `10.x.x.x`, `192.168.x.x`, and `localhost`) across custom ports. Uncover hidden or legacy HTTPS and TLS service components exposing quantum-vulnerable handshake variables.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-900/60 border-slate-800/80 backdrop-blur-xl hover:border-emerald-500/30 transition-all duration-300 shadow-xl shadow-slate-950/50">
              <CardContent className="p-8">
                <div className="p-3 w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-6">
                  <Shield className="h-6 w-6" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">LQM Cryptographic Remediation</h3>
                <p className="text-slate-300 leading-relaxed text-sm">
                  Utilize our Large Quantitative Model (LQM) to automatically diagnose findings and produce granular remediation roadmap instructions, guiding migration from RSA-2048 and ECC-256 (e.g. secp256r1) to lattice-based post-quantum standards.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-900/60 border-slate-800/80 backdrop-blur-xl hover:border-emerald-500/30 transition-all duration-300 shadow-xl shadow-slate-950/50">
              <CardContent className="p-8">
                <div className="p-3 w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-6">
                  <Fingerprint className="h-6 w-6" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">Single Sign-On (SSO) & RBAC</h3>
                <p className="text-slate-300 leading-relaxed text-sm">
                  Seamlessly onboard procurement, engineering, and cybersecurity units with corporate SSO. Safeguard enterprise workflows with strict role-based access controls supporting segregated administrator, developer, and auditor profiles.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Compliance / Gating Overview */}
      <section className="py-16 px-6 bg-slate-900/30 border-y border-slate-900 relative z-10">
        <div className="max-w-4xl mx-auto text-center">
          <Server className="h-14 w-14 text-emerald-400 mx-auto mb-6" />
          <h2 className="text-3xl font-bold font-syne mb-6 text-white">NIST and CNSA 2.0 Preparedness</h2>
          <div className="grid sm:grid-cols-3 gap-6 text-left mt-10">
            <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-xl">
              <CheckCircle2 className="h-5 w-5 text-emerald-400 mb-2" />
              <h4 className="font-bold text-white text-sm mb-1">FIPS 203 Compliant</h4>
              <p className="text-xs text-slate-400">Validate targets against ML-KEM migration parameters.</p>
            </div>
            <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-xl">
              <CheckCircle2 className="h-5 w-5 text-emerald-400 mb-2" />
              <h4 className="font-bold text-white text-sm mb-1">FIPS 204 Compliant</h4>
              <p className="text-xs text-slate-400">Audit keys and certificate structures for ML-DSA transitions.</p>
            </div>
            <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-xl">
              <CheckCircle2 className="h-5 w-5 text-emerald-400 mb-2" />
              <h4 className="font-bold text-white text-sm mb-1">FIPS 205 Compliant</h4>
              <p className="text-xs text-slate-400">Evaluate stateless hash signature alternatives (SLH-DSA).</p>
            </div>
          </div>
        </div>
      </section>

      {/* Contact & Procurement Section */}
      <section className="py-24 px-6 relative z-10">
        <div className="max-w-3xl mx-auto">
          <Card className="bg-gradient-to-br from-slate-900 to-emerald-950/40 border border-emerald-500/30 rounded-2xl shadow-2xl p-8 sm:p-12 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
              <Mail className="h-40 w-40 text-emerald-400" />
            </div>

            <div className="text-center relative z-10">
              <Mail className="h-12 w-12 text-emerald-400 mx-auto mb-6" />
              <h2 className="text-3xl sm:text-4xl font-bold font-syne text-white mb-4">Contact Sales & Procurement</h2>
              <p className="text-slate-300 text-sm sm:text-base mb-8 max-w-xl mx-auto leading-relaxed">
                Need to set up custom SLA agreements, order bulk compliance assessments, or request a corporate pricing quote? Reach out to our dedicated procurement team.
              </p>

              <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-850 inline-flex flex-col sm:flex-row items-center gap-4 px-6 justify-center mx-auto mb-8 shadow-inner">
                <span className="text-slate-400 text-sm">Official Inquiries:</span>
                <a
                  href="mailto:quantc.info@gmail.com?subject=QuantCAI%20Enterprise%20Procurement%20Inquiry"
                  className="text-emerald-400 hover:text-emerald-300 font-mono font-semibold text-lg transition-colors underline decoration-dotted"
                >
                  quantc.info@gmail.com
                </a>
              </div>

              <div>
                <a
                  href="mailto:quantc.info@gmail.com?subject=QuantCAI%20Enterprise%20Procurement%20Inquiry"
                  className="inline-flex items-center justify-center gap-2.5 px-8 py-3.5 rounded-lg bg-emerald-500 text-slate-950 font-bold hover:bg-emerald-400 shadow-lg shadow-emerald-500/25 transition-all duration-300"
                >
                  <Mail className="h-5 w-5" />
                  Email Procurement Team
                </a>
              </div>
            </div>
          </Card>
        </div>
      </section>

      <Footer />
    </div>
  );
}
