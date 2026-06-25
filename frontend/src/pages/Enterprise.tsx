import { usePageTracking } from '@/hooks/usePageTracking';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Shield, Zap, Network, Fingerprint, Mail, ArrowRight, Server, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { SEO } from '@/components/SEO';

export default function Enterprise() {
  usePageTracking('enterprise');

  return (
    <div className="min-h-screen relative overflow-hidden bg-transparent text-white">
      <SEO 
        title="Enterprise Quantum Computing & PQC Solutions - QuantCAI" 
        description="Assess, map, and remediate legacy cryptographic dependencies across your organization's infrastructure with QuantCAI's sovereign post-quantum suite." 
      />
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
              href="mailto:support@quantcai.in?subject=QuantCAI%20Enterprise%20PQC%20Compliance%20Request"
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

      {/* Enterprise SEO Section */}
      <section className="py-20 px-6 relative z-10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold font-syne mb-4">Enterprise-Grade Quantum Simulation for Strategic Advantage</h2>
            <p className="text-slate-400 max-w-2xl mx-auto leading-relaxed">
              As quantum processing capabilities rapidly scale, the window for enterprises to safely investigate and adopt quantum solutions is closing. Chief Technology Officers and security leaders face a dual challenge: investing R&D into quantum algorithms without wasting capital on inefficient computing time, while simultaneously preparing for the cryptographic shifts required by NIST's Post-Quantum Cryptography (PQC) standards. You need a scalable, secure, and cost-effective infrastructure to build your quantum readiness strategy.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <Card className="bg-slate-900/60 border-slate-800/80 backdrop-blur-xl hover:border-emerald-500/30 transition-all duration-300 shadow-xl shadow-slate-950/50">
              <CardContent className="p-8">
                <div className="p-3 w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-6">
                  <Network className="h-6 w-6" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">1. De-Risk Quantum Development Cycles</h3>
                <p className="text-slate-300 leading-relaxed text-sm">
                  Relying exclusively on premium, time-metered QPU hardware for early-stage algorithmic development is an inefficient use of budget. Our enterprise quantum simulator allows your data science and cryptography teams to build, validate, and extensively debug complex 30+ qubit architectures locally before pushing to live hardware. Reduce execution errors, prevent wasted API calls, and ensure algorithmic viability at zero variable compute cost.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-900/60 border-slate-800/80 backdrop-blur-xl hover:border-emerald-500/30 transition-all duration-300 shadow-xl shadow-slate-950/50">
              <CardContent className="p-8">
                <div className="p-3 w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-6">
                  <Zap className="h-6 w-6" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">2. Automated Circuit Optimization for Maximum ROI</h3>
                <p className="text-slate-300 leading-relaxed text-sm">
                  Quantum compute time is expensive. Our platform features an exclusive, enterprise-only Circuit Optimizer that programmatically reduces the depth and gate-count of your algorithms. By stripping out redundant operations prior to hardware execution, we dramatically reduce the decoherence risk and output higher fidelity results, directly translating to simulated cost savings and maximized ROI on your quantum hardware expenditure.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-900/60 border-slate-800/80 backdrop-blur-xl hover:border-emerald-500/30 transition-all duration-300 shadow-xl shadow-slate-950/50">
              <CardContent className="p-8">
                <div className="p-3 w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-6">
                  <Shield className="h-6 w-6" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">3. Secure Architecture & PQC Readiness</h3>
                <p className="text-slate-300 leading-relaxed text-sm">
                  Deploying quantum applications requires stringent data protection. QuantCAI operates within enterprise-grade security boundaries, allowing your teams to collaborate on proprietary algorithms safely. Furthermore, our platform is actively aligning with NIST standards for Post-Quantum Cryptography, ensuring that the simulations you run today help you build cryptographic bills of materials (CBOMs) to secure your data tomorrow.
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

      {/* Conversational Lead Generation Block */}
      <section className="py-24 px-6 relative z-10">
        <div className="max-w-4xl mx-auto">
          <Card className="bg-gradient-to-br from-slate-900 to-emerald-950/40 border border-emerald-500/40 rounded-3xl shadow-2xl p-8 sm:p-14 relative overflow-hidden group hover:border-emerald-500/60 transition-all duration-500">
            <div className="absolute top-0 right-0 p-4 opacity-[0.03] pointer-events-none group-hover:scale-110 transition-transform duration-700">
              <Mail className="h-64 w-64 text-emerald-400" />
            </div>

            <div className="text-center relative z-10">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 mb-6 drop-shadow-[0_0_15px_rgba(52,211,153,0.3)]">
                <Zap className="h-8 w-8" />
              </div>
              <h2 className="text-4xl sm:text-5xl font-bold font-syne text-white mb-6 leading-tight">
                Let's architect your <br className="hidden sm:block"/> <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-500">post-quantum future.</span>
              </h2>
              <p className="text-slate-300 text-lg sm:text-xl mb-10 max-w-2xl mx-auto leading-relaxed font-light">
                Every enterprise infrastructure is unique. Tell us about your current stack, compliance goals, and SLA requirements. Our quantum engineering team will review your needs and schedule a custom technical demo within 24 hours.
              </p>

              <div className="bg-slate-950/60 rounded-2xl p-6 border border-emerald-500/20 max-w-lg mx-auto mb-10 shadow-inner">
                <p className="text-slate-400 text-sm mb-4 font-mono uppercase tracking-widest font-semibold">Direct Engineering Contact</p>
                <a
                  href="mailto:support@quantcai.in?subject=QuantCAI%20Enterprise%20Integration%20Request&body=Hi%20QuantCAI%20Team%2C%0A%0AWe%20are%20interested%20in%20discussing%20an%20enterprise%20integration%20and%20custom%20SLA.%20Here%20is%20a%20brief%20overview%20of%20our%20current%20infrastructure%20and%20needs%3A%0A%0A%5BPlease%20describe%20your%20needs%20here%5D%0A%0AWe%20would%20like%20to%20schedule%20a%20technical%20demo.%0A%0AThank%20you%2C%0A%5BYour%20Name%5D"
                  className="inline-block text-2xl sm:text-3xl font-syne font-bold text-emerald-400 hover:text-emerald-300 transition-colors border-b-2 border-emerald-500/30 hover:border-emerald-400 pb-1"
                >
                  support@quantcai.in
                </a>
              </div>

              <div>
                <a
                  href="mailto:support@quantcai.in?subject=QuantCAI%20Enterprise%20Integration%20Request&body=Hi%20QuantCAI%20Team%2C%0A%0AWe%20are%20interested%20in%20discussing%20an%20enterprise%20integration%20and%20custom%20SLA.%20Here%20is%20a%20brief%20overview%20of%20our%20current%20infrastructure%20and%20needs%3A%0A%0A%5BPlease%20describe%20your%20needs%20here%5D%0A%0AWe%20would%20like%20to%20schedule%20a%20technical%20demo.%0A%0AThank%20you%2C%0A%5BYour%20Name%5D"
                  className="inline-flex items-center justify-center gap-3 px-10 py-5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 text-slate-950 font-bold text-lg hover:from-emerald-500 hover:to-teal-500 shadow-xl shadow-emerald-500/25 hover:shadow-emerald-500/40 hover:-translate-y-1 transition-all duration-300"
                >
                  <Mail className="h-6 w-6" />
                  Email Us Your Requirements
                </a>
              </div>
              <p className="mt-6 text-sm text-slate-500 font-mono">No forms, no friction. Just direct access to our core team.</p>
            </div>
          </Card>
        </div>
      </section>

      <Footer />
    </div>
  );
}
