"use strict";

const tenths = (value) => (value === null || value === undefined)
  ? null
  : (value / 10.0).toFixed(1);

const label = (row) => new Date(row.utc).toLocaleTimeString();

async function getJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("request failed: " + path);
  }
  return response.json();
}

function renderNodeRows(rows) {
  const body = document.querySelector("#nodes tbody");
  body.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    [row.node, tenths(row.temp_tenths), tenths(row.hum_tenths), row.rssi]
      .forEach((cell) => {
        const td = document.createElement("td");
        td.textContent = cell === null ? "-" : cell;
        tr.appendChild(td);
      });
    body.appendChild(tr);
  });
}

function renderEventRows(rows) {
  const body = document.querySelector("#events tbody");
  body.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    [String(row.utc).slice(0, 19), row.node, row.kind, row.detail]
      .forEach((cell) => {
        const td = document.createElement("td");
        td.textContent = cell === null ? "-" : cell;
        tr.appendChild(td);
      });
    body.appendChild(tr);
  });
}

function buildChart(rows) {
  const context = document.getElementById("climate");
  const temps = rows.map((row) => tenths(row.temp_tenths));
  const hums = rows.map((row) => tenths(row.hum_tenths));
  const labels = rows.map((row) => label(row));
  return new Chart(context, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        { label: "Temp C", data: temps, borderColor: "#39ff88",
          backgroundColor: "rgba(57,255,136,0.15)", tension: 0.3 },
        { label: "Humidity %", data: hums, borderColor: "#7fd8e0",
          backgroundColor: "rgba(127,216,224,0.15)", tension: 0.3 }
      ]
    },
    options: {
      responsive: true,
      animation: false,
      scales: { y: { grid: { color: "#123" }, ticks: { color: "#6f8f7c" } },
                x: { grid: { color: "#123" }, ticks: { color: "#6f8f7c" } } },
      plugins: { legend: { labels: { color: "#f2f5ff" } } }
    }
  });
}

async function refresh(chart) {
  const frames = await getJson("/api/telemetry");
  const events = await getJson("/api/events");
  renderNodeRows(frames.slice(-12).reverse());
  renderEventRows(events);
  chart.data.labels = frames.map((row) => label(row));
  chart.data.datasets[0].data = frames.map((row) => tenths(row.temp_tenths));
  chart.data.datasets[1].data = frames.map((row) => tenths(row.hum_tenths));
  chart.update();
}

async function boot() {
  const frames = await getJson("/api/telemetry");
  const chart = buildChart(frames);
  await refresh(chart);
  window.setInterval(() => refresh(chart), 5000);
}

boot().catch((error) => console.error(error));
