import React, { useEffect, useRef } from 'react';

export default function Starfield() {
    const canvasRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let width = 0;
        let height = 0;

        const setupCanvas = () => {
            if (!canvas || !ctx) return;

            // Handle High DPI (Retina) displays for crisp stars
            const dpr = window.devicePixelRatio || 1;

            // Use window geometry for logic to ensure full screen coverage
            const w = window.innerWidth;
            const h = window.innerHeight;

            canvas.width = w * dpr;
            canvas.height = h * dpr;

            // Scale context to ensure drawing operations match CSS pixels
            ctx.scale(dpr, dpr);

            // Update physics bounds
            width = w;
            height = h;
        };

        // Initial setup
        setupCanvas();

        const stars = [];
        const numStars = 800; // Original was 800
        const depth = 2000;
        let shootingStar = { active: false, x: 0, y: 0, vx: 0, vy: 0, life: 0 };

        // Initialize stars
        for (let i = 0; i < numStars; i++) {
            stars.push({
                x: (Math.random() - 0.5) * width * 2,
                y: (Math.random() - 0.5) * height * 2,
                z: Math.random() * depth,
                o: Math.random(),
            });
        }

        let animationFrameId;

        const render = () => {
            if (!canvas || !ctx) return;

            // Clear with deep space black/blue tint
            ctx.fillStyle = "#020204"; // Matches Xierra background
            ctx.fillRect(0, 0, width, height);

            // Draw Nebula effects (static or slowly moving background layers)
            // We simulate this by drawing large radial gradients
            const drawNebula = (x, y, radius, color) => {
                const grad = ctx.createRadialGradient(x, y, 0, x, y, radius);
                grad.addColorStop(0, color);
                grad.addColorStop(1, "transparent");
                ctx.fillStyle = grad;
                ctx.beginPath();
                ctx.arc(x, y, radius, 0, Math.PI * 2);
                ctx.fill();
            }

            // Purple nebula top right
            drawNebula(width * 0.8, height * 0.2, 500, "rgba(76, 29, 149, 0.15)");
            // Cyan nebula bottom left
            drawNebula(width * 0.2, height * 0.8, 600, "rgba(8, 145, 178, 0.1)");
            // Blue center deep
            drawNebula(width * 0.5, height * 0.5, 800, "rgba(30, 58, 138, 0.05)");

            const cx = width / 2;
            const cy = height / 2;
            const speed = 0.5;

            for (const star of stars) {
                star.z -= speed;

                if (star.z <= 0) {
                    star.z = depth;
                    star.x = (Math.random() - 0.5) * width * 2;
                    star.y = (Math.random() - 0.5) * height * 2;
                }

                const k = 128.0 / star.z;
                const px = star.x * k + cx;
                const py = star.y * k + cy;

                if (px >= 0 && px <= width && py >= 0 && py <= height) {
                    const size = (1 - star.z / depth) * 2.5;
                    const alpha = 1 - (star.z / depth);

                    ctx.beginPath();
                    ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
                    ctx.arc(px, py, size / 2, 0, Math.PI * 2);
                    ctx.fill();
                }
            }

            // Shooting Star Logic
            if (shootingStar.active) {
                shootingStar.x += shootingStar.vx;
                shootingStar.y += shootingStar.vy;
                if (
                    shootingStar.x < -100 || shootingStar.x > width + 100 ||
                    shootingStar.y < -100 || shootingStar.y > height + 100) {
                    shootingStar.active = false;
                } else {
                    const tailX = shootingStar.x - shootingStar.vx * 15;
                    const tailY = shootingStar.y - shootingStar.vy * 15;

                    const gradient = ctx.createLinearGradient(shootingStar.x, shootingStar.y, tailX, tailY);
                    gradient.addColorStop(0, `rgba(255, 255, 255, ${shootingStar.life})`);
                    gradient.addColorStop(1, "rgba(255, 255, 255, 0)");

                    ctx.lineWidth = 2;
                    ctx.strokeStyle = gradient;
                    ctx.beginPath();
                    ctx.moveTo(shootingStar.x, shootingStar.y);
                    ctx.lineTo(tailX, tailY);
                    ctx.stroke();

                    ctx.fillStyle = "white";
                    ctx.beginPath();
                    ctx.arc(shootingStar.x, shootingStar.y, 1.5, 0, Math.PI * 2);
                    ctx.fill();
                }
            } else {
                if (Math.random() < 0.001) {
                    shootingStar.active = true;
                    shootingStar.life = 1.0;

                    const side = Math.floor(Math.random() * 4);
                    if (side === 0) {
                        shootingStar.x = Math.random() * width;
                        shootingStar.y = 0;
                        shootingStar.vx = (Math.random() - 0.5) * 10;
                        shootingStar.vy = Math.random() * 10 + 5;
                    } else if (side === 1) {
                        shootingStar.x = width;
                        shootingStar.y = Math.random() * height;
                        shootingStar.vx = -(Math.random() * 10 + 5);
                        shootingStar.vy = (Math.random() - 0.5) * 10;
                    } else if (side === 2) {
                        shootingStar.x = Math.random() * width;
                        shootingStar.y = height;
                        shootingStar.vx = (Math.random() - 0.5) * 10;
                        shootingStar.vy = -(Math.random() - 0.5) * 10;
                    } else {
                        shootingStar.x = 0;
                        shootingStar.y = Math.random() * height;
                        shootingStar.vx = Math.random() * 10 + 5;
                        shootingStar.vy = (Math.random() - 0.5) * 10;
                    }
                }
            }

            animationFrameId = requestAnimationFrame(render);
        };

        render();

        const handleResize = () => {
            setupCanvas();
        };

        window.addEventListener('resize', handleResize);

        return () => {
            cancelAnimationFrame(animationFrameId);
            window.removeEventListener('resize', handleResize);
        };

    }, []);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 z-0 pointer-events-none"
            style={{ background: 'black' }}
        />
    );
}
