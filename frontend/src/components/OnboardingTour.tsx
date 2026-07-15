import React, { useState, useEffect } from 'react';
import { Rocket, Shield, Atom, Bot, ChevronRight, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

const TOUR_STEPS = [
  {
    id: 'welcome',
    title: 'Welcome to QuantCAI 🚀',
    description: 'Your enterprise portal for Post-Quantum Cryptography and Quantum Simulation. Let\'s get you oriented.',
    icon: Rocket,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10'
  },
  {
    id: 'pqc',
    title: 'PQC Compliance Scanner',
    description: 'Scan domains, repositories, and networks for legacy cryptographic vulnerabilities before Q-Day.',
    icon: Shield,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    link: '/enterprise/pqc-scanner'
  },
  {
    id: 'simulator',
    title: 'Quantum Circuit Simulator',
    description: 'Build and test quantum algorithms with our high-performance simulator and interactive UI.',
    icon: Atom,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    link: '/circuit-builder'
  },
  {
    id: 'ai_tutor',
    title: 'QuantAI Tutor',
    description: 'Stuck on a concept? Your AI tutor is always available in the bottom right corner to assist you.',
    icon: Bot,
    color: 'text-teal-400',
    bgColor: 'bg-teal-500/10'
  }
];

export const OnboardingTour = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if the user has already seen the tour
    const hasSeenTour = localStorage.getItem('quantcai_onboarding_complete');
    if (!hasSeenTour) {
      // Small delay to let the dashboard load first
      const timer = setTimeout(() => setIsOpen(true), 1500);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleNext = () => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setCurrentStep(prev => prev + 1);
    } else {
      handleComplete();
    }
  };

  const handleComplete = () => {
    setIsOpen(false);
    localStorage.setItem('quantcai_onboarding_complete', 'true');
  };

  if (!isOpen) return null;

  const step = TOUR_STEPS[currentStep];
  const Icon = step.icon;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm transition-opacity duration-300">
      <div className="bg-slate-900 border border-slate-700/50 rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-in fade-in zoom-in-95 duration-300">
        
        {/* Progress Bar */}
        <div className="flex h-1.5 w-full bg-slate-800">
          <div 
            className="bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500 ease-out"
            style={{ width: `${((currentStep + 1) / TOUR_STEPS.length) * 100}%` }}
          />
        </div>

        <div className="p-6 sm:p-8 relative">
          {/* Skip Button */}
          <button 
            onClick={handleComplete}
            className="absolute top-4 right-4 text-slate-400 hover:text-white text-xs font-medium transition-colors"
          >
            Skip Tour
          </button>

          <div className="flex flex-col items-center text-center mt-4">
            <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-6 shadow-inner border border-white/5 ${step.bgColor}`}>
              <Icon className={`h-8 w-8 ${step.color}`} />
            </div>
            
            <h3 className="text-xl font-bold text-white mb-3">
              {step.title}
            </h3>
            
            <p className="text-slate-400 text-sm leading-relaxed mb-8">
              {step.description}
            </p>

            <div className="flex w-full gap-3">
              {step.link && (
                <Button 
                  variant="outline" 
                  className="flex-1 border-slate-700 hover:bg-slate-800 text-slate-300"
                  onClick={() => {
                    navigate(step.link!);
                    handleComplete();
                  }}
                >
                  Explore Now
                </Button>
              )}
              
              <Button 
                className={`flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white border-none ${!step.link ? 'w-full' : ''}`}
                onClick={handleNext}
              >
                {currentStep === TOUR_STEPS.length - 1 ? (
                  <>
                    Get Started <Check className="ml-2 h-4 w-4" />
                  </>
                ) : (
                  <>
                    Next <ChevronRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </div>
          
          {/* Step Indicators */}
          <div className="flex justify-center gap-2 mt-8">
            {TOUR_STEPS.map((_, idx) => (
              <div 
                key={idx} 
                className={`h-1.5 rounded-full transition-all duration-300 ${idx === currentStep ? 'w-6 bg-blue-500' : 'w-2 bg-slate-700'}`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
