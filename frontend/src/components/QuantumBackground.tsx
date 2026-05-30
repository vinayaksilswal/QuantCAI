import { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color: string;
  opacity: number;
  type: 'qubit' | 'atom' | 'entangled';
  entangledWith?: number;
  superposition: boolean;
  phase: number;
  originalVx: number;
  originalVy: number;
}

export const QuantumBackground = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const animationRef = useRef<number | undefined>(undefined);
  const mouseRef = useRef({ x: 0, y: 0, isOver: false });



  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Mouse tracking
    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current.x = e.clientX;
      mouseRef.current.y = e.clientY;
      mouseRef.current.isOver = true;
    };

    const handleMouseLeave = () => {
      mouseRef.current.isOver = false;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);

    // Initialize particles with better visibility
    const initParticles = () => {
      particlesRef.current = [];
      const particleCount = 50;

      for (let i = 0; i < particleCount; i++) {
        const vx = (Math.random() - 0.5) * 2;
        const vy = (Math.random() - 0.5) * 2;
        const particle: Particle = {
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx,
          vy,
          originalVx: vx,
          originalVy: vy,
          size: Math.random() * 3 + 2,
          color: ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b'][Math.floor(Math.random() * 5)],
          opacity: Math.random() * 0.8 + 0.2,
          type: ['qubit', 'atom', 'entangled'][Math.floor(Math.random() * 3)] as 'qubit' | 'atom' | 'entangled',
          superposition: Math.random() > 0.7,
          entangledWith: Math.random() > 0.8 ? Math.floor(Math.random() * particleCount) : undefined,
          phase: Math.random() * Math.PI * 2,
        };
        particlesRef.current.push(particle);
      }
    };

    initParticles();

    const animate = () => {
      // Clear canvas completely
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const time = Date.now() * 0.001;
      const mouse = mouseRef.current;

      particlesRef.current.forEach((particle, index) => {
        // Mouse interaction effects
        if (mouse.isOver) {
          const dx = mouse.x - particle.x;
          const dy = mouse.y - particle.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          const maxDistance = 150;

          if (distance < maxDistance) {
            const force = (maxDistance - distance) / maxDistance;
            const angle = Math.atan2(dy, dx);
            
            // Different interaction types based on particle type
            if (particle.type === 'qubit') {
              // Qubits are attracted to cursor
              particle.vx += Math.cos(angle) * force * 0.3;
              particle.vy += Math.sin(angle) * force * 0.3;
              particle.superposition = true;
              particle.opacity = Math.min(1, particle.opacity + force * 0.5);
            } else if (particle.type === 'atom') {
              // Atoms orbit around cursor
              const orbitalAngle = angle + Math.PI * 0.5;
              particle.vx += Math.cos(orbitalAngle) * force * 0.4;
              particle.vy += Math.sin(orbitalAngle) * force * 0.4;
            } else if (particle.type === 'entangled') {
              // Entangled particles repel from cursor
              particle.vx -= Math.cos(angle) * force * 0.2;
              particle.vy -= Math.sin(angle) * force * 0.2;
              particle.size = Math.max(1, particle.size + force * 2);
            }

            // Enhanced quantum effects near cursor
            if (distance < 80) {
              particle.superposition = true;
              particle.phase += force * 0.1;
            }
          } else {
            // Gradually return to original velocity when away from cursor
            particle.vx = particle.vx * 0.98 + particle.originalVx * 0.02;
            particle.vy = particle.vy * 0.98 + particle.originalVy * 0.02;
            particle.superposition = Math.random() > 0.8;
          }
        } else {
          // Return to normal behavior when mouse not present
          particle.vx = particle.vx * 0.99 + particle.originalVx * 0.01;
          particle.vy = particle.vy * 0.99 + particle.originalVy * 0.01;
        }

        // Apply velocity damping to prevent excessive speed
        particle.vx = Math.max(-5, Math.min(5, particle.vx));
        particle.vy = Math.max(-5, Math.min(5, particle.vy));

        // Update position
        particle.x += particle.vx;
        particle.y += particle.vy;

        // Bounce off edges
        if (particle.x <= 0 || particle.x >= canvas.width) {
          particle.vx *= -0.8;
          particle.originalVx *= -1;
        }
        if (particle.y <= 0 || particle.y >= canvas.height) {
          particle.vy *= -0.8;
          particle.originalVy *= -1;
        }

        // Keep particles in bounds
        particle.x = Math.max(0, Math.min(canvas.width, particle.x));
        particle.y = Math.max(0, Math.min(canvas.height, particle.y));

        // Superposition effect
        if (particle.superposition) {
          particle.opacity = 0.4 + 0.4 * Math.sin(time * 2 + particle.phase);
          particle.size = Math.max(1, 2 + 2 * Math.sin(time * 1.5 + particle.phase));
        }

        // Check for nearby particles for quantum effects
        particlesRef.current.forEach((other, otherIndex) => {
          if (index !== otherIndex) {
            const distance = Math.sqrt(
              Math.pow(particle.x - other.x, 2) + Math.pow(particle.y - other.y, 2)
            );
            
            if (distance < 80) {
              // Create superposition effect
              particle.superposition = true;
              other.superposition = true;
            }
          }
        });

        // Draw particle with enhanced visibility
        ctx.save();
        ctx.globalAlpha = particle.opacity;
        
        if (particle.type === 'qubit') {
          // Outer glow
          const gradient = ctx.createRadialGradient(
            particle.x, particle.y, 0, 
            particle.x, particle.y, particle.size * 6
          );
          gradient.addColorStop(0, particle.color + 'FF');
          gradient.addColorStop(0.3, particle.color + '80');
          gradient.addColorStop(1, 'transparent');
          
          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.arc(particle.x, particle.y, particle.size * 6, 0, Math.PI * 2);
          ctx.fill();
          
          // Inner bright core
          ctx.fillStyle = particle.color;
          ctx.shadowColor = particle.color;
          ctx.shadowBlur = 10;
          ctx.beginPath();
          ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
          
        } else if (particle.type === 'atom') {
          // Nucleus with glow
          ctx.fillStyle = particle.color;
          ctx.shadowColor = particle.color;
          ctx.shadowBlur = 8;
          ctx.beginPath();
          ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
          
          // Electron orbits with trails
          for (let i = 0; i < 2; i++) {
            const orbitRadius = particle.size * (3 + i * 2);
            const electronAngle = time * (1 + i * 0.7) + particle.phase;
            const electronX = particle.x + Math.cos(electronAngle) * orbitRadius;
            const electronY = particle.y + Math.sin(electronAngle) * orbitRadius * 0.5;
            
            // Electron trail
            ctx.strokeStyle = '#60a5fa40';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, orbitRadius, 0, Math.PI * 2);
            ctx.stroke();
            
            // Electron
            ctx.fillStyle = '#60a5fa';
            ctx.shadowColor = '#60a5fa';
            ctx.shadowBlur = 6;
            ctx.beginPath();
            ctx.arc(electronX, electronY, 2, 0, Math.PI * 2);
            ctx.fill();
            ctx.shadowBlur = 0;
          }
          
        } else if (particle.type === 'entangled') {
          // Pulsing entangled particle
          const pulseSize = particle.size * (1 + 0.7 * Math.sin(time * 4 + particle.phase));
          
          // Outer energy field
          const gradient = ctx.createRadialGradient(
            particle.x, particle.y, 0, 
            particle.x, particle.y, pulseSize * 4
          );
          gradient.addColorStop(0, '#ec4899FF');
          gradient.addColorStop(0.4, '#8b5cf680');
          gradient.addColorStop(1, 'transparent');
          
          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.arc(particle.x, particle.y, pulseSize * 4, 0, Math.PI * 2);
          ctx.fill();
          
          // Core with intense glow
          ctx.fillStyle = '#ec4899';
          ctx.shadowColor = '#ec4899';
          ctx.shadowBlur = 12;
          ctx.beginPath();
          ctx.arc(particle.x, particle.y, pulseSize, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
        }

        ctx.restore();

        // Draw entanglement connections with enhanced visibility
        if (particle.entangledWith !== undefined && particle.entangledWith < particlesRef.current.length) {
          const entangled = particlesRef.current[particle.entangledWith];
          const distance = Math.sqrt(
            Math.pow(particle.x - entangled.x, 2) + Math.pow(particle.y - entangled.y, 2)
          );

          if (distance < 300) {
            ctx.save();
            const connectionOpacity = 0.8 * (1 - distance / 300);
            ctx.globalAlpha = connectionOpacity;
            
            // Animated entanglement beam
            const gradient = ctx.createLinearGradient(particle.x, particle.y, entangled.x, entangled.y);
            gradient.addColorStop(0, '#ec4899');
            gradient.addColorStop(0.5, '#8b5cf6');
            gradient.addColorStop(1, '#ec4899');
            
            ctx.strokeStyle = gradient;
            ctx.lineWidth = 3;
            ctx.lineCap = 'round';
            ctx.shadowColor = '#ec4899';
            ctx.shadowBlur = 8;
            
            // Pulsing dash pattern
            const dashOffset = time * 20;
            ctx.setLineDash([8, 8]);
            ctx.lineDashOffset = dashOffset;
            
            ctx.beginPath();
            ctx.moveTo(particle.x, particle.y);
            ctx.lineTo(entangled.x, entangled.y);
            ctx.stroke();
            ctx.restore();
          }
        }
      });

      // Draw quantum field connections
      for (let i = 0; i < particlesRef.current.length; i++) {
        for (let j = i + 1; j < particlesRef.current.length; j++) {
          const p1 = particlesRef.current[i];
          const p2 = particlesRef.current[j];
          const distance = Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));

          if (distance < 120) {
            ctx.save();
            ctx.globalAlpha = 0.15 * (1 - distance / 120);
            ctx.strokeStyle = '#3b82f6';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
            ctx.restore();
          }
        }
      }

      // Draw cursor effect if mouse is present
      if (mouse.isOver) {
        ctx.save();
        ctx.globalAlpha = 0.3;
        const cursorGradient = ctx.createRadialGradient(
          mouse.x, mouse.y, 0,
          mouse.x, mouse.y, 100
        );
        cursorGradient.addColorStop(0, '#ffffff40');
        cursorGradient.addColorStop(0.5, '#3b82f620');
        cursorGradient.addColorStop(1, 'transparent');
        
        ctx.fillStyle = cursorGradient;
        ctx.beginPath();
        ctx.arc(mouse.x, mouse.y, 100, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  return (
    <div className="fixed inset-0 z-0" style={{ background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)' }}>
      <canvas
        ref={canvasRef}
        className="absolute top-0 left-0 w-full h-full pointer-events-none"
        style={{ 
          background: 'transparent'
        }}
      />
    </div>
  );
};
