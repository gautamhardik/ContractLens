import React, { useEffect, useRef } from 'react';

/**
 * AmbientField: Subtle 2D Canvas-based 'Contract Intelligence Field'
 * Renders faint topological constellation nodes and subtle filament connections
 * reacting dynamically to agent activity states without high GPU overhead.
 */
export default function AmbientField({ agentState = 'idle' }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Generate constellation nodes
    const nodeCount = 38;
    const nodes = Array.from({ length: nodeCount }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      radius: Math.random() * 1.5 + 0.8,
      alpha: Math.random() * 0.25 + 0.1,
      baseAlpha: Math.random() * 0.25 + 0.1,
    }));

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Multiplier based on agent state
      const isInvestigating = agentState === 'investigating' || agentState === 'comparing';
      const speedMult = isInvestigating ? 1.8 : 1.0;
      const alphaMult = isInvestigating ? 1.6 : 1.0;

      // Update and draw nodes
      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];
        node.x += node.vx * speedMult;
        node.y += node.vy * speedMult;

        if (node.x < 0) node.x = width;
        if (node.x > width) node.x = 0;
        if (node.y < 0) node.y = height;
        if (node.y > height) node.y = 0;

        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        ctx.fillStyle = isInvestigating
          ? `rgba(204, 120, 92, ${node.alpha * alphaMult * 0.9})`
          : `rgba(140, 133, 123, ${node.alpha * 0.55})`;
        ctx.fill();

        // Connect nearby nodes with delicate filaments
        for (let j = i + 1; j < nodes.length; j++) {
          const other = nodes[j];
          const dx = other.x - node.x;
          const dy = other.y - node.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 130) {
            const lineAlpha = (1 - dist / 130) * 0.05 * alphaMult;
            ctx.beginPath();
            ctx.moveTo(node.x, node.y);
            ctx.lineTo(other.x, other.y);
            ctx.strokeStyle = isInvestigating
              ? `rgba(204, 120, 92, ${lineAlpha})`
              : `rgba(140, 133, 123, ${lineAlpha})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [agentState]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        pointerEvents: 'none',
        zIndex: 0,
        opacity: 0.85
      }}
    />
  );
}
