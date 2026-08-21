const fit = window.FITTRACK || { water: 0, history: [] };
let water = fit.water || 0;
let history = fit.history || [];

const $ = (id) => document.getElementById(id);
const toast = (message) => {
    const el = $("toast");
    if (!el) return;
    el.textContent = message;
    el.classList.add("show");
    setTimeout(() => el.classList.remove("show"), 1900);
};

const dateEl = $("todayDate");
if (dateEl) {
    dateEl.textContent = new Date().toLocaleDateString(undefined, {
        weekday: "short", month: "short", day: "numeric", year: "numeric"
    });
}

function renderWater() {
    if (!$("waterCount")) return;
    const pct = Math.round((water / 8) * 100);
    $("waterCount").textContent = water;
    $("waterPercent").textContent = pct;
    $("bottleFill").style.height = `${pct}%`;
    document.querySelectorAll(".glass-btn").forEach((btn, index) => {
        btn.classList.toggle("filled", index < water);
    });
    $("waterMessage").textContent = water >= 8
        ? "Hydration goal complete! Great work. 💧"
        : `${8 - water} glass${8 - water === 1 ? "" : "es"} left to reach today's goal.`;
}

async function waterAction(action) {
    const res = await fetch("/api/water", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action })
    });
    const data = await res.json();
    if (res.ok) {
        water = data.water;
        renderWater();
        toast(action === "add" ? "Water logged 💧" : "Water updated");
    }
}

$("addWater")?.addEventListener("click", () => waterAction("add"));
$("removeWater")?.addEventListener("click", () => waterAction("remove"));

document.querySelectorAll(".glass-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
        const desired = Number(btn.dataset.index);
        while (water < desired) {
            const res = await fetch("/api/water", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "add" }) });
            const data = await res.json(); water = data.water;
        }
        while (water > desired) {
            const res = await fetch("/api/water", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "remove" }) });
            const data = await res.json(); water = data.water;
        }
        renderWater();
        toast(`Hydration set to ${water}/8`);
    });
});

$("newQuoteBtn")?.addEventListener("click", async () => {
    const res = await fetch("/api/quote");
    const data = await res.json();
    $("quoteText").animate([{ opacity: .25 }, { opacity: 1 }], { duration: 280 });
    $("quoteText").textContent = data.quote;
});

$("saveActivity")?.addEventListener("click", async () => {
    const payload = {
        steps: Number($("stepsInput").value || 0),
        active_minutes: Number($("minutesInput").value || 0),
        calories: Number($("caloriesInput").value || 0)
    };
    const res = await fetch("/api/activity", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (res.ok) {
        $("stepsStat").textContent = data.steps.toLocaleString();
        $("minutesStat").textContent = data.active_minutes;
        $("caloriesStat").textContent = data.calories;
        $("stepsProgress").style.width = `${Math.min(100, data.steps / 100)}%`;
        toast("Activity saved ✓");
    }
});

$("saveWeight")?.addEventListener("click", async () => {
    const weight = Number($("weightInput").value);
    if (!weight || weight <= 0) return toast("Enter a valid weight");
    const res = await fetch("/api/weight", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ weight })
    });
    const data = await res.json();
    if (res.ok) {
        $("weightValue").textContent = Number(data.weight).toFixed(1);
        $("bmiValue").textContent = data.bmi;
        $("bmiLabel").textContent = data.bmi_label;
        history.push({ weight: data.weight, date: new Date().toISOString().slice(0, 10) });
        history = history.slice(-7);
        drawWeightChart();
        toast("Weight updated ✓");
    }
});

function drawWeightChart() {
    const canvas = $("weightChart");
    if (!canvas) return;
    const empty = $("emptyChart");
    empty.style.display = history.length < 2 ? "grid" : "none";

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = 230 * dpr;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    const w = rect.width, h = 230;
    ctx.clearRect(0, 0, w, h);

    if (history.length < 2) return;
    const values = history.map(x => Number(x.weight));
    const min = Math.min(...values) - 1;
    const max = Math.max(...values) + 1;
    const pad = { l: 35, r: 20, t: 20, b: 32 };
    const chartW = w - pad.l - pad.r;
    const chartH = h - pad.t - pad.b;

    ctx.strokeStyle = "rgba(123, 160, 201, .11)";
    ctx.lineWidth = 1;
    for (let i = 0; i < 4; i++) {
        const y = pad.t + (chartH / 3) * i;
        ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
    }

    const points = values.map((v, i) => ({
        x: pad.l + (chartW / (values.length - 1)) * i,
        y: pad.t + chartH - ((v - min) / (max - min)) * chartH
    }));

    const gradient = ctx.createLinearGradient(0, pad.t, 0, h - pad.b);
    gradient.addColorStop(0, "rgba(54, 150, 255, .34)");
    gradient.addColorStop(1, "rgba(54, 150, 255, 0)");
    ctx.beginPath();
    ctx.moveTo(points[0].x, h - pad.b);
    points.forEach(p => ctx.lineTo(p.x, p.y));
    ctx.lineTo(points[points.length - 1].x, h - pad.b);
    ctx.closePath(); ctx.fillStyle = gradient; ctx.fill();

    ctx.beginPath();
    points.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y));
    ctx.strokeStyle = "#48a6ff"; ctx.lineWidth = 3; ctx.stroke();

    points.forEach((p, i) => {
        ctx.beginPath(); ctx.arc(p.x, p.y, 4, 0, Math.PI * 2); ctx.fillStyle = "#83caff"; ctx.fill();
        ctx.fillStyle = "#7890aa"; ctx.font = "9px Inter"; ctx.textAlign = "center";
        ctx.fillText(history[i].date.slice(5), p.x, h - 11);
    });
}

window.addEventListener("resize", drawWeightChart);
drawWeightChart();
renderWater();
