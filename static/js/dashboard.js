// SentinelAI Dashboard JavaScript
// This file adds small visual effects to the dashboard page.


// Update the live clock shown in the dashboard.
function updateLiveClock() {

    // Create a Date object for the current moment.
    const currentTime = new Date();

    // These options tell JavaScript how to format the clock string.
    const timeFormatOptions = {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    };

    // Find the clock element in the page.
    const clockElement = document.getElementById("live-clock");

    // Only update the clock if the element exists.
    if (clockElement) {
        clockElement.innerHTML = currentTime.toLocaleTimeString([], timeFormatOptions);
    }

}

// Refresh the clock every second and also show it immediately.
setInterval(updateLiveClock, 1000);
updateLiveClock();


// Animate dashboard cards when the page loads.
const dashboardCards = document.querySelectorAll(".card,.camera,.alerts,.gallery,.evidence");

dashboardCards.forEach((cardElement, index) => {

    // Start each card slightly transparent and lower on the page.
    cardElement.style.opacity = "0";
    cardElement.style.transform = "translateY(30px)";

    // Stagger the animation so the cards appear one after another.
    setTimeout(() => {

        cardElement.style.transition = ".7s ease";
        cardElement.style.opacity = "1";
        cardElement.style.transform = "translateY(0px)";

    }, index * 120);

});


// Add a glow effect when the user hovers over sidebar menu items.
document.querySelectorAll(".menu li").forEach((menuItem) => {

    menuItem.addEventListener("mouseenter", () => {
        menuItem.style.boxShadow = "0 0 20px rgba(124,58,237,.4)";
    });

    menuItem.addEventListener("mouseleave", () => {
        menuItem.style.boxShadow = "none";
    });

});


// Zoom evidence images a little when the user hovers over them.
document.querySelectorAll(".evidence img").forEach((evidenceImage) => {

    evidenceImage.addEventListener("mouseenter", () => {
        evidenceImage.style.transform = "scale(1.08)";
        evidenceImage.style.transition = ".4s";
    });

    evidenceImage.addEventListener("mouseleave", () => {
        evidenceImage.style.transform = "scale(1)";
    });

});


// Make the camera panel gently float up and down.
const cameraPanel = document.querySelector(".camera");

if (cameraPanel) {

    let animationAngle = 0;

    setInterval(() => {

        animationAngle += 0.02;

        cameraPanel.style.transform = `translateY(${Math.sin(animationAngle) * 5}px)`;

    }, 30);

}


// Create a soft glow that follows the mouse pointer.
const mouseGlow = document.createElement("div");

mouseGlow.style.position = "fixed";
mouseGlow.style.width = "280px";
mouseGlow.style.height = "280px";
mouseGlow.style.borderRadius = "50%";
mouseGlow.style.pointerEvents = "none";
mouseGlow.style.background = "radial-gradient(circle, rgba(124,58,237,.15), transparent 70%)";
mouseGlow.style.filter = "blur(18px)";
mouseGlow.style.transform = "translate(-50%,-50%)";
mouseGlow.style.zIndex = "-1";

document.body.appendChild(mouseGlow);

document.addEventListener("mousemove", (event) => {
    mouseGlow.style.left = event.clientX + "px";
    mouseGlow.style.top = event.clientY + "px";
});


// Make LOW threat values gently blink to draw attention.
const threatValueElements = document.querySelectorAll(".card h2");

threatValueElements.forEach((threatElement) => {

    if (threatElement.innerHTML.trim() === "LOW") {

        setInterval(() => {

            threatElement.style.color =
                threatElement.style.color === "#22c55e"
                    ? "#ffffff"
                    : "#22c55e";

        }, 800);

    }

});


// Add a pulsing animation to the online status dot.
const onlineDot = document.querySelector(".dot");

if (onlineDot) {

    setInterval(() => {

        onlineDot.animate([
            {
                transform: "scale(1)"
            },
            {
                transform: "scale(1.6)"
            },
            {
                transform: "scale(1)"
            }
        ], {

            duration: 1000

        });

    }, 1200);

}


// Animate numeric counters from 0 up to their final value.
function animateCounter(counterElement) {

    // Read the text inside the element and convert it into a number.
    const targetValue = Number(counterElement.innerText);

    // If the text is not a number, do nothing.
    if (isNaN(targetValue)) return;

    let currentValue = 0;

    // Split the movement into small steps so the number grows smoothly.
    const stepSize = Math.ceil(targetValue / 40);

    const counterTimer = setInterval(() => {

        currentValue += stepSize;

        if (currentValue >= targetValue) {
            counterElement.innerText = targetValue;
            clearInterval(counterTimer);
        }
        else {
            counterElement.innerText = currentValue;
        }

    }, 25);

}

document.querySelectorAll(".card h2").forEach((counterElement) => {
    animateCounter(counterElement);
});


// Print a branded message in the browser console.
console.log(
    "%cSentinelAI Command Center",
    "font-size:26px;color:#7c3aed;font-weight:bold;"
);

console.log(
    "AI Surveillance & Security Analytics Platform"
);
async function updateLiveStatus() {

    try {

        const response = await fetch("/api/status");
        const data = await response.json();

        const peopleCountElement = document.getElementById("people-count");
        const threatLevelElement = document.getElementById("threat-level");
        const cameraStatusElement = document.getElementById("camera-status");

        if (peopleCountElement) {
            peopleCountElement.innerText = data.people;
        }

        if (threatLevelElement) {
            threatLevelElement.innerText = data.threat;
        }

        if (cameraStatusElement) {
            cameraStatusElement.innerText = data.camera;
        }

    }

    catch (error) {

        console.log("Status API Error:", error);

    }

}

// Update every second
setInterval(updateLiveStatus, 1000);

// Run immediately
updateLiveStatus();

async function loadAnalyticsChart() {

    const chartCanvas = document.getElementById("alertsChart");

    if (!chartCanvas) {
        return;
    }

    const response = await fetch("/api/analytics");
    const analytics = await response.json();

    new Chart(chartCanvas, {

        type: "bar",

        data: {

            labels: analytics.labels,

            datasets: [{

                label: "Intrusions",

                data: analytics.values,

                borderWidth: 1

            }]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            scales: {
                y: {
                    beginAtZero: true
                }
            }

        }

    });

}

loadAnalyticsChart();
const searchBox = document.getElementById("search-box");

if (searchBox) {

    searchBox.addEventListener("keyup", async () => {

        const keyword = searchBox.value;

        const response = await fetch(
            `/api/search?q=${encodeURIComponent(keyword)}`
        );

        const events = await response.json();

        const gallery = document.getElementById("gallery-grid");

        if (!gallery) {
            return;
        }

gallery.innerHTML = "";

events.forEach(event => {

    gallery.innerHTML += `

        <div class="evidence">

            <img src="/${event[3]}" alt="Evidence">

            <div class="body">

                <h3>Event #${event[0]}</h3>

                <p>${event[1]}</p>

                <small>${event[2]}</small>

                <br><br>

                <div class="evidence-buttons">

                    <a href="/${event[3]}" target="_blank">
                        View
                    </a>

                    <a href="/${event[3]}" download>
                        Download
                    </a>

                </div>

            </div>

        </div>

    `;

});

    });

}