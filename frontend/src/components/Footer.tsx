import { Link } from 'react-router-dom';
import { Facebook, Linkedin, Youtube, Instagram } from 'lucide-react';
import { NewsletterForm } from './NewsletterForm';
import { LogoProcessor } from './LogoProcessor';

export const Footer = () => {
  return (
    <footer className="bg-black/50 backdrop-blur-sm border-t border-blue-600/30 relative z-10">
      <div className="px-8 py-16">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-8">
          {/* Logo and Description */}
          <div className="col-span-2 md:col-span-1 lg:col-span-1">
            <div className="flex items-center space-x-3 mb-4">
              <LogoProcessor
                originalSrc="/lovable-uploads/56a0d2c9-73da-4624-bfb1-2bb520c4a4e3.png"
                alt="QuantCAI Logo"
                className="h-10 hover:scale-105 transition-all duration-300"
                style={{
                  filter: 'drop-shadow(0 0 10px rgba(59, 130, 246, 0.5)) brightness(1.1) contrast(1.2) saturate(1.1)',
                  mixBlendMode: 'screen'
                }}
              />
            </div>
            <p className="text-qc-muted leading-relaxed">
              Shaping Tomorrow's Quantum Future Today.
            </p>
          </div>

          {/* Navigation Links */}
          <div>
            <h3 className="text-qc-text font-semibold mb-4">Navigation</h3>
            <div className="space-y-3">
              <Link to="/" className="flex items-center min-h-[44px] py-1 text-qc-muted hover:text-qc-text transition-colors">
                Home
              </Link>
              <span className="block text-qc-muted hover:text-qc-text transition-colors cursor-pointer">
                Solutions
              </span>
              <Link to="/vision" className="flex items-center min-h-[44px] py-1 text-qc-muted hover:text-qc-text transition-colors">
                Vision
              </Link>
              <Link to="/learn" className="flex items-center min-h-[44px] py-1 text-qc-muted hover:text-qc-text transition-colors">
                Learn
              </Link>
              <Link to="/soon" className="flex items-center min-h-[44px] py-1 text-qc-muted hover:text-qc-text transition-colors">
                Soon
              </Link>
              <Link to="/get-started" className="flex items-center min-h-[44px] py-1 text-qc-muted hover:text-qc-text transition-colors">
                Get Started
              </Link>
            </div>
          </div>

          {/* Legal Links */}
          <div>
            <h3 className="text-qc-text font-semibold mb-4">Legal</h3>
            <div className="space-y-3">
              <Link to="/terms" className="flex items-center min-h-[44px] py-1 text-qc-muted hover:text-qc-text transition-colors">
                Terms & Conditions
              </Link>
              <Link to="/privacy" className="flex items-center min-h-[44px] py-1 text-qc-muted hover:text-qc-text transition-colors">
                Privacy Policy
              </Link>
              <Link to="/refund-policy" className="flex items-center min-h-[44px] py-1 text-qc-muted hover:text-qc-text transition-colors">
                Refund Policy
              </Link>
              <Link to="/security" className="flex items-center min-h-[44px] py-1 text-qc-muted hover:text-qc-text transition-colors">
                Security & Compliance
              </Link>
            </div>
          </div>

          {/* Newsletter */}
          <div>
            <h3 className="text-qc-text font-semibold mb-4">Subscribe to Our Newsletter</h3>
            <NewsletterForm compact />
          </div>

          {/* Social */}
          <div>
            <h3 className="text-qc-text font-semibold mb-4">Follow Us On:</h3>
            <div className="flex space-x-4">
              <a 
                href="https://www.facebook.com/profile.php?id=61583324510921" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="grid place-items-center min-w-[44px] min-h-[44px] -m-2 rounded-lg text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover transition-colors"
                aria-label="Facebook"
              >
                <Facebook className="h-6 w-6" />
              </a>
              <a 
                href="https://www.instagram.com/quantcai.info/reels/" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="grid place-items-center min-w-[44px] min-h-[44px] -m-2 rounded-lg text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover transition-colors"
                aria-label="Instagram"
              >
                <Instagram className="h-6 w-6" />
              </a>
              <a 
                href="https://www.linkedin.com/company/quantcai/?viewAsMember=true" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="grid place-items-center min-w-[44px] min-h-[44px] -m-2 rounded-lg text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover transition-colors"
                aria-label="LinkedIn"
              >
                <Linkedin className="h-6 w-6" />
              </a>
              <a 
                href="https://www.youtube.com/channel/UCtOTdDiQXMQ9RUOXGnFrSvQ" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="grid place-items-center min-w-[44px] min-h-[44px] -m-2 rounded-lg text-qc-muted hover:text-qc-text hover:bg-qc-surface-hover transition-colors"
                aria-label="YouTube"
              >
                <Youtube className="h-6 w-6" />
              </a>
            </div>
          </div>
        </div>

        {/* Platform Disclaimer Section */}
        <div className="border-t border-blue-700/30 mt-12 pt-6 text-center">
          <p className="text-gray-500 text-[11px] leading-relaxed max-w-4xl mx-auto">
            AI was used to assist in code optimization and drafting foundational educational materials.
            The entire platform has been rigorously tested, audited, and finalized by a human developer.
          </p>
          <p className="text-gray-500 text-[10px] leading-relaxed mt-4 max-w-4xl mx-auto italic">
            Disclaimer: WarriorPlus is used to help manage the sale of products on this site. While WarriorPlus helps facilitate the sale, all payments are made directly to the product vendor and NOT WarriorPlus. Thus, all product questions, support inquiries and/or refund requests must be sent to the vendor. WarriorPlus's role should not be construed as an endorsement, approval or review of these products or any claim, statement or opinion used in the marketing of these products.
          </p>
        </div>

        {/* Compliance Policy & Disclaimer Section */}
        <div className="border-t border-blue-700/30 mt-8 pt-8 text-left text-xs text-slate-400">
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h4 className="font-bold text-slate-300 mb-2 uppercase tracking-wider">Privacy Policy</h4>
              <p className="leading-relaxed">
                We collect personal information (name, email, billing details via WarriorPlus/payment processors) and usage data (simulation history, AI chat volume) to manage your subscription and prevent system abuse. We share data only with necessary processing services and do not sell your data. For requests or data deletion, contact <a href="mailto:quantc.info@gmail.com" className="text-qc-accent hover:underline">quantc.info@gmail.com</a>.
              </p>
            </div>
            <div>
              <h4 className="font-bold text-slate-300 mb-2 uppercase tracking-wider">Income & Results Disclaimer</h4>
              <p className="leading-relaxed">
                Earnings, traffic, or ranking examples on this page are exceptional results and not guarantees. Your success depends entirely on your own effort, technical skill, budget, and market conditions. Quantum computing tools involve technical risks, and we do not guarantee specific monetary or performance outcomes.
              </p>
            </div>
          </div>
        </div>

        {/* Copyright & Support Email Bar at absolute bottom */}
        <div className="border-t border-blue-700/50 mt-10 pt-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0 text-sm font-bold">
            <p className="text-slate-300">© 2024–{new Date().getFullYear()} QuantCAI. All rights reserved.</p>
            <p className="text-slate-300">
              Support Email: <a href="mailto:quantc.info@gmail.com" className="text-qc-accent hover:text-qc-muted transition-colors ml-1">
                quantc.info@gmail.com
              </a>
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};
