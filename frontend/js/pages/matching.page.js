import { listCandidates } from "../services/candidates.service.js";
import { getMatchesForCandidate } from "../services/matching.service.js";
import { showToast } from "../components/toast.js";

export async function renderMatchingPage() {
  const view = document.getElementById("view-matching");
  view.innerHTML = `
    <h2>Matching</h2>
    <p class="muted">Pick a candidate to find their best-matching jobs .</p>
    <select id="matching-candidate-select"></select>
    <div class="section" style="margin-top:12px;">
      <h4>Filters</h4>
      <label>Location</label>
      <select id="matching-filter-location">
        <option value="">Any</option>
        <option value="Tunis">Tunis</option>
        <option value="Sousse">Sousse</option>
        <option value="Sfax">Sfax</option>
        <option value="Monastir">Monastir</option>
        <option value="Ariana">Ariana</option>
        <option value="Remote">Remote</option>
      </select>
      <label>Remote policy</label>
      <select id="matching-filter-remote">
        <option value="">Any</option>
        <option value="On-site">On-site</option>
        <option value="Hybrid">Hybrid</option>
        <option value="Remote">Remote</option>
      </select>
      <label>Experience level</label>
      <select id="matching-filter-experience">
        <option value="">Any</option>
        <option value="Junior">Junior</option>
        <option value="Mid">Mid</option>
        <option value="Senior">Senior</option>
      </select>
    </div>
    <button id="matching-run-btn" class="primary">Find matches</button>
    <div id="matching-results"></div>
  `;

  const candidates = await listCandidates();
  const select = document.getElementById("matching-candidate-select");
  select.innerHTML = candidates.length
    ? candidates
        .map((c) => `<option value="${c.id}">${c.name}</option>`)
        .join("")
    : `<option value="">No candidates yet</option>`;

  document
    .getElementById("matching-run-btn")
    .addEventListener("click", async () => {
      const candidateId = select.value;
      if (!candidateId) return;
      const filters = {
        location: document.getElementById("matching-filter-location").value,
        remote_policy: document.getElementById("matching-filter-remote").value,
        experience_level: document.getElementById("matching-filter-experience")
          .value,
      };
      const resultsEl = document.getElementById("matching-results");
      resultsEl.innerHTML = `<p class="muted small">Searching...</p>`;
      try {
        const matches = await getMatchesForCandidate(candidateId, filters);
        resultsEl.innerHTML = "";
        if (!matches.length) {
          resultsEl.innerHTML = `<p class="muted small">No matches found.</p>`;
          return;
        }
        matches.forEach((m) => {
          const row = document.createElement("div");
          row.className = "candidate-row";
          row.innerHTML = `
          <div>
            <strong>${m.job_title}</strong> — score: ${m.score ?? "N/A"}
            <div class="row-sub">${m.justification || ""}</div>
          </div>
          <span class="badge ${m.category}">${m.verdict}</span>
        `;
          resultsEl.appendChild(row);
        });
      } catch (err) {
        showToast(err.message, "error");
      }
    });
}
