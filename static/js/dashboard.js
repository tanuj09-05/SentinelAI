function updateLiveClock() {
    const clock = document.getElementById("live-clock");
    if (clock) {
        clock.innerText = new Date().toLocaleTimeString([], {hour: "2-digit", minute: "2-digit", second: "2-digit"});
    }
}
setInterval(updateLiveClock, 1000);
updateLiveClock();

function animateCounter(el, target) {
    if (isNaN(target)) return;
    let current = parseInt(el.innerText) || 0;
    if (current === target) return;
    
    const diff = target - current;
    const step = Math.ceil(Math.abs(diff) / 10) * Math.sign(diff);
    
    const timer = setInterval(() => {
        current += step;
        if ((step > 0 && current >= target) || (step < 0 && current <= target)) {
            el.innerText = target;
            clearInterval(timer);
        } else {
            el.innerText = current;
        }
    }, 40);
}

let currentTotalEvents = -1;
let systemChartInstance = null;
let previousCameraStatus = "offline";

async function updateLiveStatus() {
    try {
        const resp = await fetch("/api/status");
        if (!resp.ok) return;
        const data = await resp.json();

        const peopleEl = document.getElementById("people-count");
        if (peopleEl) animateCounter(peopleEl, data.people);
        
        const threatEl = document.getElementById("threat-level");
        const threatIcon = document.getElementById("threat-icon");
        
        if (threatEl && threatIcon) {
            threatEl.innerText = data.threat;
            if (data.threat === "SAFE") {
                threatEl.className = "text-success";
                threatIcon.className = "icon-success";
                threatIcon.setAttribute("data-lucide", "shield-check");
            } else if (data.loitering_alert) {
                threatEl.innerText = "LOITERING";
                threatEl.className = "text-danger";
                threatIcon.className = "icon-danger";
                threatIcon.setAttribute("data-lucide", "alert-triangle");
            } else {
                threatEl.className = "text-danger";
                threatIcon.className = "icon-danger";
                threatIcon.setAttribute("data-lucide", "shield-alert");
            }
            lucide.createIcons();
        }
        
        const eventsEl = document.getElementById("total-events");
        if (eventsEl && data.total_events !== undefined) {
            if (currentTotalEvents !== -1 && currentTotalEvents !== data.total_events) {
                animateCounter(eventsEl, data.total_events);
                refreshDashboardData();
            } else if (currentTotalEvents === -1) {
                animateCounter(eventsEl, data.total_events);
            }
            currentTotalEvents = data.total_events;
        }
    } catch (e) {
        console.warn("Status API Error:", e);
    }
}

async function fetchSystemMetrics() {
    try {
        const resp = await fetch("/api/system_metrics");
        if (!resp.ok) return;
        const metrics = await resp.json();
        
        const updateBar = (id, metric, max, unit) => {
            const valEl = document.getElementById(`${id}-value`);
            const fillEl = document.querySelector(`.${id}-fill`);
            if (!valEl || !fillEl) return;
            
            if (metric === undefined || metric === null || isNaN(metric) || (metric <= 0 && id !== "cpu" && id !== "ram")) {
                valEl.innerText = "N/A";
                fillEl.style.width = "0%";
                fillEl.style.background = "var(--text-muted)";
                return;
            }
            
            valEl.innerText = `${metric}${unit}`;
            const width = Math.min((metric / max) * 100, 100);
            fillEl.style.width = `${width}%`;
            
            if (width > 85) fillEl.style.background = "var(--danger)";
            else if (width > 60) fillEl.style.background = "var(--warning)";
            else fillEl.style.background = "var(--cyan)";
        };
        
        updateBar("cpu", metrics.cpu, 100, "%");
        updateBar("ram", metrics.ram, 100, "%");
        updateBar("latency", metrics.latency, 200, "ms");
        updateBar("fps", metrics.fps, 60, "");
        
        const fpsOverlay = document.getElementById("overlay-fps");
        if (fpsOverlay) fpsOverlay.innerText = `FPS: ${metrics.fps}`;

        const statuses = document.querySelectorAll(".status-item .indicator");
        if (statuses.length === 6) {
            const services = ["ai", "camera", "database", "auth", "email", "analytics"];
            const serviceNames = ["AI Engine", "Camera Service", "Database", "Authentication", "Email Service", "Analytics Engine"];
            services.forEach((s, idx) => {
                const statusClass = metrics.services[s] === "not configured" ? "warning" : metrics.services[s];
                statuses[idx].className = `indicator ${statusClass}`;
                
                const next = statuses[idx].nextSibling;
                if (next && next.nodeType === 3) {
                    next.nodeValue = ` ${serviceNames[idx]} - ${metrics.services[s].toUpperCase()}`;
                }
            });
        }
        
        const cameraStatusText = document.getElementById("camera-status");
        if (cameraStatusText && metrics.services.camera) {
            const camStatus = metrics.services.camera.toLowerCase();
            const camStatusUpper = camStatus.toUpperCase();
            
            cameraStatusText.innerText = camStatusUpper;
            cameraStatusText.className = camStatusUpper === "ONLINE" ? "text-success" : "text-danger";

            if (camStatus === "online" && previousCameraStatus !== "online") {
                const mainImg = document.getElementById("main-camera-img");
                if (mainImg) {
                    mainImg.src = `/video_feed?t=${new Date().getTime()}`;
                }
            }
            previousCameraStatus = camStatus;
        }
    } catch (e) {
        console.warn("System Metrics Error:", e);
    }
}

async function refreshDashboardData() {
    const alertsList = document.getElementById("recent-alerts-list");
    if (alertsList) {
        try {
            const resp = await fetch("/api/alerts");
            if (resp.ok) {
                const alerts = await resp.json();
                let html = "";
                alerts.slice(0, 6).forEach(a => {
                    const isHigh = a.event.includes("Intrusion");
                    html += `
                        <div class="alert-item ${isHigh ? 'severity-high' : ''}">
                            <div class="alert-icon"><i data-lucide="${isHigh ? 'user-x' : 'info'}"></i></div>
                            <div class="alert-content">
                                <strong>Event #${a.id}</strong>
                                <p>${a.event}</p>
                                <small><i data-lucide="clock" style="width:12px"></i> ${a.time}</small>
                            </div>
                        </div>
                    `;
                });
                alertsList.innerHTML = html;
                lucide.createIcons();
            }
        } catch (e) { }
    }
    
    const searchBox = document.getElementById("search-box");
    if (searchBox) {
        searchBox.dispatchEvent(new KeyboardEvent('keyup'));
    }
    
    loadAnalyticsChart();
}

async function loadAnalyticsChart() {
    const canvas = document.getElementById("alertsChart");
    if (!canvas) return;
    
    try {
        const resp = await fetch("/api/analytics");
        if (!resp.ok) return;
        const data = await resp.json();
        
        if (systemChartInstance) {
            systemChartInstance.destroy();
        }
        
        systemChartInstance = new Chart(canvas, {
            type: "line",
            data: {
                labels: data.labels,
                datasets: [{
                    label: "Security Events",
                    data: data.values,
                    borderColor: "#7c3aed",
                    backgroundColor: "rgba(124, 58, 237, 0.2)",
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: "#22d3ee",
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: "#f8fafc" }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: "rgba(255,255,255,0.05)" },
                        ticks: { color: "#94a3b8" }
                    },
                    x: {
                        grid: { color: "rgba(255,255,255,0.05)" },
                        ticks: { color: "#94a3b8" }
                    }
                }
            }
        });
    } catch (e) { }
}

const camSelect = document.getElementById("camera-select");
if (camSelect) {
    camSelect.addEventListener("change", (e) => {
        const val = e.target.value;
        const img = document.getElementById("main-camera-img");
        const placeholder = document.getElementById("offline-placeholder");
        const badge = document.querySelector(".badge-cam");
        
        if (badge) badge.innerText = `CAM 0${val}`;
        
        if (val === "1") {
            img.style.display = "block";
            placeholder.style.display = "none";
            document.querySelector(".badge-live").style.display = "flex";
        } else {
            img.style.display = "none";
            placeholder.style.display = "flex";
            document.querySelector(".badge-live").style.display = "none";
        }
    });
}

const searchBox = document.getElementById("search-box");
if (searchBox) {
    searchBox.addEventListener("keyup", async () => {
        try {
            const resp = await fetch(`/api/search?q=${encodeURIComponent(searchBox.value)}`);
            if (!resp.ok) return;
            const events = await resp.json();
            const gallery = document.getElementById("gallery-grid");
            if (!gallery) return;
            
            let html = "";
            events.slice(0,8).forEach(e => {
                html += `
                <div class="evidence-card">
                    <div class="evidence-img-wrapper">
                        <img src="/${e[3]}" alt="Evidence">
                        <div class="evidence-overlay">
                            <a href="/${e[3]}" target="_blank" class="btn-icon"><i data-lucide="eye"></i></a>
                            <a href="/${e[3]}" download class="btn-icon"><i data-lucide="download"></i></a>
                        </div>
                    </div>
                    <div class="evidence-body">
                        <h4>Event #${e[0]}</h4>
                        <p><i data-lucide="tag"></i> ${e[1]}</p>
                        <small><i data-lucide="clock"></i> ${e[2]}</small>
                    </div>
                </div>`;
            });
            gallery.innerHTML = html || `<div class="empty-state"><i data-lucide="image-off"></i><p>No evidence found.</p></div>`;
            lucide.createIcons();
        } catch (e) {}
    });
}

setInterval(updateLiveStatus, 1000);
setInterval(fetchSystemMetrics, 2000);
updateLiveStatus();
fetchSystemMetrics();
loadAnalyticsChart();