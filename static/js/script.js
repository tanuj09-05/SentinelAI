document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener("click", function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute("href"));
        if (target) {
            target.scrollIntoView({ behavior: "smooth" });
        }
    });
});

const navbar = document.querySelector(".navbar");

window.addEventListener("scroll", () => {
    if (window.scrollY > 50) {
        navbar.style.background = "rgba(5,8,22,.85)";
        navbar.style.backdropFilter = "blur(20px)";
        navbar.style.boxShadow = "0 10px 30px rgba(0,0,0,.35)";
    } else {
        navbar.style.background = "rgba(5,8,22,.45)";
        navbar.style.boxShadow = "none";
    }
});

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = "1";
            entry.target.style.transform = "translateY(0px)";
        }
    });
}, { threshold: 0.15 });

document.querySelectorAll(".section,.feature,.glass-card").forEach(el => {
    el.style.opacity = "0";
    el.style.transform = "translateY(50px)";
    el.style.transition = ".8s ease";
    observer.observe(el);
});

const glow = document.createElement("div");
glow.style.position = "fixed";
glow.style.width = "250px";
glow.style.height = "250px";
glow.style.borderRadius = "50%";
glow.style.pointerEvents = "none";
glow.style.background = "radial-gradient(circle, rgba(124,58,237,.18), transparent 70%)";
glow.style.filter = "blur(12px)";
glow.style.transform = "translate(-50%,-50%)";
glow.style.zIndex = "-1";
document.body.appendChild(glow);

document.addEventListener("mousemove", (e) => {
    glow.style.left = e.clientX + "px";
    glow.style.top = e.clientY + "px";
});

const card = document.querySelector(".glass-card");
if (card) {
    let angle = 0;
    setInterval(() => {
        angle += 0.02;
        card.style.transform = `translateY(${Math.sin(angle) * 8}px)`;
    }, 30);
}

document.querySelectorAll(".primary-btn,.secondary-btn").forEach(btn => {
    btn.addEventListener("mouseenter", () => {
        btn.style.transform = "translateY(-4px) scale(1.03)";
    });
    btn.addEventListener("mouseleave", () => {
        btn.style.transform = "translateY(0px) scale(1)";
    });
});

const badge = document.querySelector(".badge");
if (badge) {
    const text = badge.innerText;
    badge.innerText = "";
    let i = 0;
    function type() {
        if (i < text.length) {
            badge.innerText += text.charAt(i);
            i++;
            setTimeout(type, 40);
        }
    }
    type();
}

for (let i = 0; i < 20; i++) {
    const particle = document.createElement("div");
    particle.style.position = "fixed";
    particle.style.width = "4px";
    particle.style.height = "4px";
    particle.style.background = "#7c3aed";
    particle.style.borderRadius = "50%";
    particle.style.opacity = Math.random();
    particle.style.left = Math.random() * window.innerWidth + "px";
    particle.style.top = Math.random() * window.innerHeight + "px";
    particle.style.animation = `float ${4 + Math.random() * 5}s infinite ease-in-out`;
    particle.style.pointerEvents = "none";
    particle.style.zIndex = "-2";
    document.body.appendChild(particle);
}

const style = document.createElement("style");
style.innerHTML = `
@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-25px); }
    100% { transform: translateY(0px); }
}
`;
document.head.appendChild(style);

console.log("%cSentinelAI", "color:#7c3aed;font-size:30px;font-weight:bold;");
console.log("AI Surveillance & Security Intelligence Platform");