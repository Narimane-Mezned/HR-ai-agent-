import { getReportSummary } from "../services/reports.service.js";

export async function renderReportingPage() {
  const view = document.getElementById("view-reporting");
  view.innerHTML = `
    <h2>Reporting</h2>
    <div class="section">
      <h4>LLM usage</h4>
      <div id="report-stats"></div>
    </div>
    <div class="section">
      <h4>Pipeline funnel per job</h4>
      <div id="report-funnel"></div>
    </div>
  `;

  const data = await getReportSummary();
  const s = data.call_stats || {};
  document.getElementById("report-stats").innerHTML = `
    <p>Total LLM calls: <strong>${s.total_calls || 0}</strong></p>
    <p>Total tokens: <strong>${(s.total_prompt_tokens || 0) + (s.total_completion_tokens || 0)}</strong></p>
    <p>Avg latency: <strong>${s.avg_latency_ms ? Math.round(s.avg_latency_ms) + " ms" : "N/A"}</strong></p>
    <p>Estimated cost: <strong>$${(s.total_cost || 0).toFixed(4)}</strong></p>
  `;

  const funnel = data.funnel || [];
  document.getElementById("report-funnel").innerHTML = funnel.length
    ? `<table>
        <tr><th>Job</th><th>Total</th><th>Suitable</th><th>Borderline</th><th>Not suitable</th></tr>
        ${funnel.map((f) => `<tr><td>${f.job_title}</td><td>${f.total}</td><td>${f.suitable}</td><td>${f.borderline}</td><td>${f.not_suitable}</td></tr>`).join("")}
      </table>`
    : `<p class="muted small">No screening data yet.</p>`;
}
