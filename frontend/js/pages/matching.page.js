import { listCandidates } from "../services/candidates.service.js";
import { getMatchesForCandidate } from "../services/matching.service.js";
import { showToast } from "../components/toast.js";

export async function renderMatchingPage() {
  const view = document.getElementById("view-matching");
  view.innerHTML = `
    <h2>Matching</h2>
    <p class="muted">Pick a candidate to find their best-matching jobs (RAG-based retrieval).</p>
    <select id="matching-candidate-select"></select>
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
      const resultsEl = document.getElementById("matching-results");
      resultsEl.innerHTML = `<p class="muted small">Searching...</p>`;
      try {
        const matches = await getMatchesForCandidate(candidateId);
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
