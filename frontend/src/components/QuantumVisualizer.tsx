
import { useEffect, useRef } from 'react';
import { QubitState } from '@/pages/QuantumStates';

interface QuantumVisualizerProps {
  qubitState: QubitState;
}

export const QuantumVisualizer = ({ qubitState }: QuantumVisualizerProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas with gradient background
    const gradient = ctx.createRadialGradient(canvas.width / 2, canvas.height / 2, 0, canvas.width / 2, canvas.height / 2, canvas.width / 2);
    gradient.addColorStop(0, 'rgba(15, 15, 35, 0.95)');
    gradient.addColorStop(1, 'rgba(26, 26, 46, 0.98)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const sphereRadius = 140;

    // Create modern sphere with multiple layers and glowing effects
    const drawModernSphere = () => {
      // Outer glow
      const outerGlow = ctx.createRadialGradient(centerX, centerY, sphereRadius - 20, centerX, centerY, sphereRadius + 40);
      outerGlow.addColorStop(0, 'rgba(59, 130, 246, 0.1)');
      outerGlow.addColorStop(1, 'rgba(59, 130, 246, 0)');
      ctx.fillStyle = outerGlow;
      ctx.beginPath();
      ctx.arc(centerX, centerY, sphereRadius + 40, 0, 2 * Math.PI);
      ctx.fill();

      // Main sphere with gradient
      const sphereGradient = ctx.createRadialGradient(centerX - 30, centerY - 30, 0, centerX, centerY, sphereRadius);
      sphereGradient.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
      sphereGradient.addColorStop(0.7, 'rgba(59, 130, 246, 0.1)');
      sphereGradient.addColorStop(1, 'rgba(59, 130, 246, 0.05)');
      ctx.fillStyle = sphereGradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, sphereRadius, 0, 2 * Math.PI);
      ctx.fill();

      // Sphere outline with glow
      ctx.shadowColor = 'rgba(59, 130, 246, 0.8)';
      ctx.shadowBlur = 10;
      ctx.strokeStyle = 'rgba(147, 197, 253, 0.6)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(centerX, centerY, sphereRadius, 0, 2 * Math.PI);
      ctx.stroke();
      ctx.shadowBlur = 0;
    };

    drawModernSphere();

    // Modern grid lines with perspective
    const drawGrid = () => {
      ctx.strokeStyle = 'rgba(147, 197, 253, 0.3)';
      ctx.lineWidth = 1;

      // Equatorial circles
      for (let i = 0; i < 3; i++) {
        const radius = sphereRadius * (0.3 + i * 0.35);
        ctx.beginPath();
        ctx.ellipse(centerX, centerY, radius, radius * 0.25, 0, 0, 2 * Math.PI);
        ctx.stroke();
      }

      // Meridian lines
      for (let i = 0; i < 6; i++) {
        const angle = (i * Math.PI) / 3;
        ctx.beginPath();
        ctx.ellipse(centerX, centerY, sphereRadius, sphereRadius * 0.25, angle, 0, 2 * Math.PI);
        ctx.stroke();
      }

      // Vertical axis with gradient
      const axisGradient = ctx.createLinearGradient(centerX, centerY - sphereRadius, centerX, centerY + sphereRadius);
      axisGradient.addColorStop(0, 'rgba(34, 197, 94, 0.8)');
      axisGradient.addColorStop(1, 'rgba(239, 68, 68, 0.8)');
      ctx.strokeStyle = axisGradient;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(centerX, centerY - sphereRadius);
      ctx.lineTo(centerX, centerY + sphereRadius);
      ctx.stroke();

      // Horizontal axis
      ctx.strokeStyle = 'rgba(147, 197, 253, 0.6)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(centerX - sphereRadius, centerY);
      ctx.lineTo(centerX + sphereRadius, centerY);
      ctx.stroke();
    };

    drawGrid();

    // Modern labels with glow effect
    const drawLabels = () => {
      ctx.font = 'bold 18px "SF Pro Display", -apple-system, sans-serif';
      ctx.textAlign = 'center';
      ctx.shadowColor = 'rgba(255, 255, 255, 0.8)';
      ctx.shadowBlur = 5;

      // |0⟩ label
      ctx.fillStyle = '#22c55e';
      ctx.fillText('|0⟩', centerX, centerY - sphereRadius - 20);

      // |1⟩ label
      ctx.fillStyle = '#ef4444';
      ctx.fillText('|1⟩', centerX, centerY + sphereRadius + 35);

      // |+⟩ and |-⟩ labels
      ctx.fillStyle = '#3b82f6';
      ctx.fillText('|+⟩', centerX + sphereRadius + 25, centerY + 8);
      ctx.fillText('|-⟩', centerX - sphereRadius - 25, centerY + 8);
      
      ctx.shadowBlur = 0;
    };

    drawLabels();

    // Calculate qubit position with improved physics
    const { alpha, beta, phase } = qubitState;
    const prob0 = alpha * alpha;
    const prob1 = beta * beta;
    
    // Convert to spherical coordinates
    const theta = 2 * Math.acos(Math.abs(alpha));
    const phi = phase;

    // Convert to Cartesian coordinates with better projection
    const x = sphereRadius * Math.sin(theta) * Math.cos(phi);
    const y = sphereRadius * Math.sin(theta) * Math.sin(phi);
    const z = sphereRadius * Math.cos(theta);

    // Enhanced 3D projection
    const projX = centerX + x * 0.8;
    const projY = centerY - z * 0.9;

    // Draw state vector with modern styling
    const drawStateVector = () => {
      // Vector shadow
      ctx.shadowColor = 'rgba(245, 158, 11, 0.5)';
      ctx.shadowBlur = 15;
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(projX, projY);
      ctx.stroke();

      // Vector glow
      ctx.strokeStyle = 'rgba(245, 158, 11, 0.3)';
      ctx.lineWidth = 8;
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(projX, projY);
      ctx.stroke();

      ctx.shadowBlur = 0;

      // State point with multiple layers
      const pointGradient = ctx.createRadialGradient(projX, projY, 0, projX, projY, 15);
      pointGradient.addColorStop(0, '#fbbf24');
      pointGradient.addColorStop(0.7, '#f59e0b');
      pointGradient.addColorStop(1, '#d97706');
      
      ctx.fillStyle = pointGradient;
      ctx.beginPath();
      ctx.arc(projX, projY, 12, 0, 2 * Math.PI);
      ctx.fill();

      // Point outline
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(projX, projY, 12, 0, 2 * Math.PI);
      ctx.stroke();

      // Pulse effect
      ctx.strokeStyle = 'rgba(245, 158, 11, 0.4)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(projX, projY, 18, 0, 2 * Math.PI);
      ctx.stroke();
    };

    drawStateVector();

    // Modern probability visualization
    const drawProbabilityBars = () => {
      const barWidth = 60;
      const barMaxHeight = 120;
      const barSpacing = 30;
      
      // |0⟩ probability bar
      const bar0Height = prob0 * barMaxHeight;
      const bar0X = 40;
      const bar0Y = canvas.height - 80;

      // Bar background
      ctx.fillStyle = 'rgba(34, 197, 94, 0.2)';
      ctx.fillRect(bar0X, bar0Y - barMaxHeight, barWidth, barMaxHeight);

      // Bar fill with gradient
      const bar0Gradient = ctx.createLinearGradient(bar0X, bar0Y, bar0X, bar0Y - bar0Height);
      bar0Gradient.addColorStop(0, '#22c55e');
      bar0Gradient.addColorStop(1, '#16a34a');
      ctx.fillStyle = bar0Gradient;
      ctx.fillRect(bar0X, bar0Y - bar0Height, barWidth, bar0Height);

      // Bar border
      ctx.strokeStyle = '#22c55e';
      ctx.lineWidth = 2;
      ctx.strokeRect(bar0X, bar0Y - barMaxHeight, barWidth, barMaxHeight);

      // |1⟩ probability bar
      const bar1Height = prob1 * barMaxHeight;
      const bar1X = canvas.width - 100;
      const bar1Y = canvas.height - 80;

      // Bar background
      ctx.fillStyle = 'rgba(239, 68, 68, 0.2)';
      ctx.fillRect(bar1X, bar1Y - barMaxHeight, barWidth, barMaxHeight);

      // Bar fill with gradient
      const bar1Gradient = ctx.createLinearGradient(bar1X, bar1Y, bar1X, bar1Y - bar1Height);
      bar1Gradient.addColorStop(0, '#ef4444');
      bar1Gradient.addColorStop(1, '#dc2626');
      ctx.fillStyle = bar1Gradient;
      ctx.fillRect(bar1X, bar1Y - bar1Height, barWidth, bar1Height);

      // Bar border
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 2;
      ctx.strokeRect(bar1X, bar1Y - barMaxHeight, barWidth, barMaxHeight);

      // Labels and values
      ctx.font = 'bold 14px "SF Pro Display", -apple-system, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillStyle = '#ffffff';
      ctx.fillText('|0⟩', bar0X + barWidth/2, bar0Y + 20);
      ctx.fillText(prob0.toFixed(3), bar0X + barWidth/2, bar0Y - barMaxHeight - 10);
      
      ctx.fillText('|1⟩', bar1X + barWidth/2, bar1Y + 20);
      ctx.fillText(prob1.toFixed(3), bar1X + barWidth/2, bar1Y - barMaxHeight - 10);
    };

    drawProbabilityBars();

  }, [qubitState]);

  return (
    <div className="flex justify-center">
      <canvas 
        ref={canvasRef} 
        width={500} 
        height={400}
        className="border border-blue-400/30 rounded-2xl bg-gradient-to-br from-slate-900/50 to-blue-900/30 backdrop-blur-sm shadow-2xl shadow-blue-500/20"
      />
    </div>
  );
};
