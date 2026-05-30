import { Link } from 'react-router-dom';
import { Facebook, Twitter, Linkedin } from 'lucide-react';
import { NewsletterForm } from './NewsletterForm';
import { LogoProcessor } from './LogoProcessor';

export const Footer = () => {
  return (
    <footer className="bg-black/50 backdrop-blur-sm border-t border-blue-600/30 relative z-10">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid lg:grid-cols-4 gap-8">
          {/* Logo and Description */}
          <div className="lg:col-span-1">
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
            <p className="text-blue-200 leading-relaxed">
              Shaping Tomorrow's Quantum Future Today.
            </p>
          </div>

          {/* Links */}
          <div className="lg:col-span-1">
            <h3 className="text-white font-semibold mb-4">Navigation</h3>
            <div className="space-y-3">
              <Link to="/" className="block text-blue-200 hover:text-white transition-colors">
                Home
              </Link>
              <span className="block text-blue-200 hover:text-white transition-colors cursor-pointer">
                Solutions
              </span>
              <Link to="/vision" className="block text-blue-200 hover:text-white transition-colors">
                Vision
              </Link>
              <Link to="/learn" className="block text-blue-200 hover:text-white transition-colors">
                Learn
              </Link>
              <Link to="/soon" className="block text-blue-200 hover:text-white transition-colors">
                Soon
              </Link>
              <Link to="/get-started" className="block text-blue-200 hover:text-white transition-colors">
                Get Started
              </Link>
            </div>
          </div>

          {/* Newsletter */}
          <div className="lg:col-span-1">
            <h3 className="text-white font-semibold mb-4">Subscribe to Our Newsletter</h3>
            <NewsletterForm compact />
          </div>

          {/* Social */}
          <div className="lg:col-span-1">
            <h3 className="text-white font-semibold mb-4">Follow Us On:</h3>
            <div className="flex space-x-4">
              <a href="#" className="text-blue-200 hover:text-white transition-colors">
                <Facebook className="h-6 w-6" />
              </a>
              <a href="#" className="text-blue-200 hover:text-white transition-colors">
                <Twitter className="h-6 w-6" />
              </a>
              <a href="#" className="text-blue-200 hover:text-white transition-colors">
                <Linkedin className="h-6 w-6" />
              </a>
            </div>
          </div>
        </div>

        <div className="border-t border-blue-700/50 mt-12 pt-8 text-center">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <p className="text-blue-200">© 2024 by QuantCAI</p>
            <a href="mailto:quantc.info@gmail.com" className="text-blue-300 hover:text-white transition-colors">
              quantc.info@gmail.com
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};
