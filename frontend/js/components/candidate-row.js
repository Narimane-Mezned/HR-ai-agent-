export function renderCandidateRow(screening, onSchedule) {
  const row = document.createElement("div");
  row.className = "candidate-row";
  row.innerHTML = `
    <div>
      <strong>${screening.candidate_name}</strong> — score: ${screening.score ?? "N/A"}
      <div class="row-sub">${screening.justification || ""}</div>
    </div>
    <div class="row-actions">
      <span class="badge ${screening.category}">${screening.verdict}</span>
      <button class="secondary small">Schedule</button>
    </div>
  `;
  row
    .querySelector("button")
    .addEventListener("click", () =>
      onSchedule(screening.candidate_id, screening.candidate_name),
    );
  return row;
}
