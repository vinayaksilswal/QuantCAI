/**
 * =============================================================================
 * QuantCAI — Dynamic pSEO Simulation Landing Page
 * =============================================================================
 * Renders a unique, SEO-optimized landing page for each quantum algorithm or
 * PQC concept based on the slug parameter from the URL.
 *
 * Uses the pseo_catalog.json data to populate:
 *   - Meta tags (title, description) for SEO
 *   - Hero section with algorithm-specific content
 *   - Embedded circuit builder with pre-loaded template
 *   - Structured data (JSON-LD) for Google Rich Results
 *
 * Route: /simulate/:slug
 * Example: /simulate/grovers-algorithm
 *
 * Copyright (c) 2026 QuantCAI — All rights reserved.
 * =============================================================================
 */

import { useParams, Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import {
  ArrowRight,
  BookOpen,
  Code2,
  Cpu,
  Shield,
  Zap,
  ExternalLink,
} from 'lucide-react';
import pseoCatalog from '@/data/pseo_catalog.json';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';

interface PseoEntry {
  slug: string;
  title: string;
  h1: string;
  metaDescription: string;
  circuit: string;
  category: string;
  difficulty: string;
  qubits: number;
  gateCount: number;
  keywords: string[];
}

const difficultyColors: Record<string, string> = {
  beginner: 'bg-green-500/10 text-green-400 border-green-500/20',
  intermediate: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  advanced: 'bg-red-500/10 text-red-400 border-red-500/20',
};

const categoryIcons: Record<string, typeof Cpu> = {
  quantum: Cpu,
  cybersecurity: Shield,
};

const SimulatePage = () => {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();

  const entry = (pseoCatalog as PseoEntry[]).find(
    (p) => p.slug === slug
  );

  if (!entry) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#0a0f1d] text-white">
        <h1 className="text-4xl font-bold mb-4">Page Not Found</h1>
        <p className="text-gray-400 mb-8">
          This simulation doesn't exist. Explore our catalog instead.
        </p>
        <Link
          to="/tools"
          className="rounded-xl bg-blue-600 px-6 py-3 font-medium text-white hover:bg-blue-500 transition-colors"
        >
          Browse All Simulators
        </Link>
      </div>
    );
  }

  const CategoryIcon = categoryIcons[entry.category] || Cpu;

  // JSON-LD Structured Data for Google Rich Results
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'WebApplication',
    name: entry.title,
    description: entry.metaDescription,
    url: `https://quantcai.in/simulate/${entry.slug}`,
    applicationCategory: 'EducationalApplication',
    operatingSystem: 'Web Browser',
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
    },
    provider: {
      '@type': 'Organization',
      name: 'QuantCAI',
      url: 'https://quantcai.in',
    },
  };

  return (
    <>
      <Helmet>
        <title>{entry.title} | QuantCAI</title>
        <meta name="description" content={entry.metaDescription} />
        <meta name="keywords" content={entry.keywords.join(', ')} />
        <link
          rel="canonical"
          href={`https://quantcai.in/simulate/${entry.slug}`}
        />

        {/* Open Graph */}
        <meta property="og:title" content={entry.title} />
        <meta property="og:description" content={entry.metaDescription} />
        <meta property="og:type" content="website" />
        <meta
          property="og:url"
          content={`https://quantcai.in/simulate/${entry.slug}`}
        />

        {/* Twitter Card */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={entry.title} />
        <meta name="twitter:description" content={entry.metaDescription} />

        {/* JSON-LD */}
        <script type="application/ld+json">
          {JSON.stringify(jsonLd)}
        </script>
      </Helmet>

      <Navbar />

      <main className="min-h-screen bg-[#0a0f1d] pt-20">
        {/* Hero Section */}
        <section className="relative overflow-hidden border-b border-white/5 px-4 py-16 sm:py-24">
          {/* Background gradient */}
          <div className="absolute inset-0 bg-gradient-to-b from-blue-600/5 via-transparent to-transparent" />
          <div className="absolute -left-40 top-20 h-80 w-80 rounded-full bg-blue-600/10 blur-[100px]" />
          <div className="absolute -right-40 top-40 h-80 w-80 rounded-full bg-purple-600/10 blur-[100px]" />

          <div className="relative mx-auto max-w-4xl text-center">
            {/* Breadcrumb */}
            <nav className="mb-6 flex items-center justify-center gap-2 text-sm text-gray-500">
              <Link to="/" className="hover:text-white transition-colors">
                Home
              </Link>
              <span>/</span>
              <Link to="/tools" className="hover:text-white transition-colors">
                Tools
              </Link>
              <span>/</span>
              <span className="text-gray-300">{entry.title}</span>
            </nav>

            {/* Badges */}
            <div className="mb-6 flex flex-wrap items-center justify-center gap-3">
              <span
                className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${
                  difficultyColors[entry.difficulty] || difficultyColors.beginner
                }`}
              >
                <Zap className="h-3 w-3" />
                {entry.difficulty.charAt(0).toUpperCase() + entry.difficulty.slice(1)}
              </span>

              <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-gray-300">
                <CategoryIcon className="h-3 w-3" />
                {entry.category === 'cybersecurity' ? 'Cybersecurity' : 'Quantum'}
              </span>

              {entry.qubits > 0 && (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-gray-300">
                  <Code2 className="h-3 w-3" />
                  {entry.qubits} qubits · {entry.gateCount} gates
                </span>
              )}
            </div>

            {/* H1 */}
            <h1 className="mb-6 text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
              {entry.h1}
            </h1>

            {/* Description */}
            <p className="mx-auto mb-10 max-w-2xl text-lg leading-relaxed text-gray-400">
              {entry.metaDescription}
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap items-center justify-center gap-4">
              <button
                onClick={() =>
                  navigate('/circuit-builder', {
                    state: { template: entry.circuit },
                  })
                }
                className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 px-8 py-3.5 text-sm font-semibold text-white shadow-lg shadow-blue-500/25 transition-all hover:shadow-blue-500/40 hover:brightness-110 active:scale-[0.98]"
              >
                Launch Simulator
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </button>

              <Link
                to="/learn"
                className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-8 py-3.5 text-sm font-semibold text-white transition-all hover:bg-white/10 active:scale-[0.98]"
              >
                <BookOpen className="h-4 w-4" />
                Learn the Theory
              </Link>
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section className="mx-auto max-w-5xl px-4 py-16 sm:py-24">
          <div className="grid gap-6 md:grid-cols-3">
            <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-8 transition-colors hover:border-white/10 hover:bg-white/[0.04]">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-500/10">
                <Cpu className="h-6 w-6 text-blue-400" />
              </div>
              <h3 className="mb-2 text-lg font-semibold text-white">
                Real-Time Simulation
              </h3>
              <p className="text-sm leading-relaxed text-gray-400">
                Run quantum circuits instantly in your browser with our
                GPU-accelerated state vector simulator. No local install needed.
              </p>
            </div>

            <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-8 transition-colors hover:border-white/10 hover:bg-white/[0.04]">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-purple-500/10">
                <Code2 className="h-6 w-6 text-purple-400" />
              </div>
              <h3 className="mb-2 text-lg font-semibold text-white">
                Qiskit Export
              </h3>
              <p className="text-sm leading-relaxed text-gray-400">
                Export your circuits as production-ready Qiskit Python code or
                OpenQASM 2.0 — ready for IBM Quantum hardware.
              </p>
            </div>

            <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-8 transition-colors hover:border-white/10 hover:bg-white/[0.04]">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-green-500/10">
                <Shield className="h-6 w-6 text-green-400" />
              </div>
              <h3 className="mb-2 text-lg font-semibold text-white">
                {entry.category === 'cybersecurity'
                  ? 'PQC Security Analysis'
                  : 'Step-by-Step Visualization'}
              </h3>
              <p className="text-sm leading-relaxed text-gray-400">
                {entry.category === 'cybersecurity'
                  ? 'Understand the quantum threat to current cryptography and how NIST PQC standards provide protection.'
                  : 'Watch quantum states evolve gate-by-gate with interactive Bloch sphere visualization and probability histograms.'}
              </p>
            </div>
          </div>
        </section>

        {/* Related Simulations */}
        <section className="border-t border-white/5 px-4 py-16 sm:py-24">
          <div className="mx-auto max-w-5xl">
            <h2 className="mb-8 text-2xl font-bold text-white">
              Related Simulations
            </h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {(pseoCatalog as PseoEntry[])
                .filter(
                  (p) =>
                    p.slug !== entry.slug &&
                    p.category === entry.category
                )
                .slice(0, 3)
                .map((related) => (
                  <Link
                    key={related.slug}
                    to={`/simulate/${related.slug}`}
                    className="group flex items-start gap-3 rounded-xl border border-white/5 bg-white/[0.02] p-5 transition-all hover:border-white/10 hover:bg-white/[0.04]"
                  >
                    <div className="mt-0.5 flex-shrink-0">
                      <ExternalLink className="h-4 w-4 text-gray-500 transition-colors group-hover:text-blue-400" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-white group-hover:text-blue-400 transition-colors">
                        {related.title}
                      </h3>
                      <p className="mt-1 text-xs text-gray-500 line-clamp-2">
                        {related.metaDescription}
                      </p>
                    </div>
                  </Link>
                ))}
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
};

export default SimulatePage;
