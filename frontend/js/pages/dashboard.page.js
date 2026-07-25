import { getDashboardSummary } from "../services/dashboard.service.js";

let charts = {};

export async function renderDashboardPage() {
  const view = document.getElementById("view-dashboard");
  view.innerHTML = `
    <h2>Dashboard</h2>
    <div id="dash-profile" class="profile-bar"></div>
    <div class="stat-grid" id="dash-stats"></div>
    <div class="chart-grid">
      <div class="section"><h4>Pipeline funnel per job</h4><div class="chart-box"><canvas id="chart-funnel"></canvas></div></div>
      <div class="section"><h4>Average score per job</h4><div class="chart-box"><canvas id="chart-avg-score"></canvas></div></div>
      <div class="section chart-wide"><h4>Top skills among suitable candidates</h4><div class="chart-box"><canvas id="chart-skills"></canvas></div></div>
    </div>
  `;

  const data = await getDashboardSummary();
  renderProfile(data.profile);
  renderStats(data);
  renderFunnelChart(data.per_job);
  renderAvgScoreChart(data.per_job);
  renderSkillsChart(data.top_skills);
}

function renderProfile(profile) {
  const el = document.getElementById("dash-profile");
  if (!profile) {
    el.innerHTML = `<p class="muted small">Profile not found.</p>`;
    return;
  }
  el.innerHTML = `<strong>${profile.username}</strong><span class="muted"> — ${profile.company_name || "No company set"}</span>`;
}

function renderStats(data) {
  const items = [
    { label: "Jobs", value: data.totals.jobs },
    { label: "Screenings", value: data.totals.screenings },
    { label: "Avg. score", value: data.avg_score ?? "—" },
    { label: "Avg. years exp.", value: data.avg_years_experience ?? "—" },
  ];
  document.getElementById("dash-stats").innerHTML = items
    .map(
      (i) =>
        `<div class="stat-card"><div class="stat-value">${i.value}</div><div class="stat-label">${i.label}</div></div>`,
    )
    .join("");
}
function destroy(key) {
  if (charts[key]) charts[key].destroy();
}

function renderFunnelChart(perJob) {
  destroy("funnel");
  const ctx = document.getElementById("chart-funnel");
  if (!perJob.length) {
    ctx.parentElement.innerHTML = `<p class="muted small">No data yet.</p>`;
    return;
  }
  charts.funnel = new Chart(ctx, {
    type: "bar",
    data: {
      labels: perJob.map((j) => j.job_title),
      datasets: [
        {
          label: "Suitable",
          data: perJob.map((j) => j.suitable),
          backgroundColor: "#a8d8c9",
        },
        {
          label: "Borderline",
          data: perJob.map((j) => j.borderline),
          backgroundColor: "#f6dfa3",
        },
        {
          label: "Not suitable",
          data: perJob.map((j) => j.not_suitable),
          backgroundColor: "#f0b8b8",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { stacked: true },
        y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } },
      },
      plugins: { legend: { position: "bottom" } },
    },
  });
}

function renderAvgScoreChart(perJob) {
  destroy("avgScore");
  const ctx = document.getElementById("chart-avg-score");
  if (!perJob.length) {
    ctx.parentElement.innerHTML = `<p class="muted small">No data yet.</p>`;
    return;
  }
  charts.avgScore = new Chart(ctx, {
    type: "bar",
    data: {
      labels: perJob.map((j) => j.job_title),
      datasets: [
        {
          label: "Avg. score",
          data: perJob.map((j) => j.avg_score || 0),
          backgroundColor: "#b8cbe8",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true, max: 100 } },
      plugins: { legend: { display: false } },
    },
  });
}

function renderSkillsChart(topSkills) {
  destroy("skills");
  const ctx = document.getElementById("chart-skills");
  if (!topSkills.length) {
    ctx.parentElement.innerHTML = `<p class="muted small">No suitable candidates yet.</p>`;
    return;
  }
  charts.skills = new Chart(ctx, {
    type: "bar",
    data: {
      labels: topSkills.map((s) => s.skill),
      datasets: [
        {
          label: "Occurrences",
          data: topSkills.map((s) => s.count),
          backgroundColor: "#cbb8e8",
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
    },
  });
}
