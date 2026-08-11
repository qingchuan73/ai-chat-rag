import { useEffect, useRef } from "react";

interface Particle {
    x: number;
    y: number;
    vx: number;
    vy: number;
    radius: number;
    alpha: number;
    alphaSpeed: number;
}

function FloatingParticles() {
    const canvasRef = useRef<HTMLCanvasElement | null>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let animationFrameId: number;
        let particles: Particle[] = [];
        const particleCount = 60; // 粒子数量控制

        // 适应窗口大小
        const resizeCanvas = () => {
            if (canvas) {
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
            }
        };
        resizeCanvas();
        window.addEventListener("resize", resizeCanvas);

        // 初始化粒子
        const initParticles = () => {
            particles = [];
            for (let i = 0; i < particleCount; i++) {
                particles.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    vx: (Math.random() - 0.5) * 0.3, // 水平飘动速度 (极慢)
                    vy: (Math.random() - 0.5) * 0.3 - 0.15, // 垂直向上漂移主导
                    radius: Math.random() * 2 + 0.5, // 粒子大小 0.5px ~ 2.5px
                    alpha: Math.random() * 0.5 + 0.1, // 初始透明度
                    alphaSpeed: Math.random() * 0.005 + 0.002, // 呼吸闪烁速度
                });
            }
        };
        initParticles();

        // 动画主循环
        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            particles.forEach((p) => {
                // 绘制微粒
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(255, 255, 255, ${p.alpha})`;
                ctx.fill();

                // 更新位置
                p.x += p.vx;
                p.y += p.vy;

                // 呼吸闪烁效果
                p.alpha += p.alphaSpeed;
                if (p.alpha > 0.6 || p.alpha < 0.1) {
                    p.alphaSpeed = -p.alphaSpeed;
                }

                // 边界碰撞重置（从边缘淡入淡出）
                if (p.x < 0) p.x = canvas.width;
                if (p.x > canvas.width) p.x = 0;
                if (p.y < 0) p.y = canvas.height;
                if (p.y > canvas.height) p.y = 0;
            });

            animationFrameId = requestAnimationFrame(animate);
        };
        animate();

        return () => {
            window.removeEventListener("resize", resizeCanvas);
            cancelAnimationFrame(animationFrameId);
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                pointerEvents: "none", // 保证不遮挡鼠标点击
                zIndex: 0,
            }}
        />
    );
}

export default FloatingParticles;