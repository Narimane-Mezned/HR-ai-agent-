import {
  listCommunicationCandidates,
  decideCommunication,
} from "../services/communication.service.js";
import { openScheduleModal } from "./scheduling.page.js";
import { showToast } from "../components/toast.js";

const DECISION_LABELS = {
  preselection_refused: "REFUSED",
  rejected: "REFUSED",
  preselection_accepted: "PENDING INTERVIEW",
  hired: "HIRED",
};

const DECISION_CLASSES = {
  preselection_refused: "not_suitable",
  rejected: "not_suitable",
  preselection_accepted: "borderline",
  hired: "suitable",
};

export async function renderCommunicationPage() {
  const view = document.getElementById("view-communication");
  view.innerHTML = `
    <h2>Communication</h2>
    <p class="muted">All screened candidates across your jobs. Decisions send an automatic, personalized email.</p>
    <div id="communication-list"></div>
  `;
  await loadCommunicationList();
}

function renderActions(s) {
  if (!s.decision) {
    return `
      <button class="secondary small" data-action="preselection_accept">Preselection Accept</button>
      <button class="secondary small" data-action="preselection_refuse">Preselection Refuse</button>
    `;
  }
  if (s.decision === "preselection_accepted") {
    return `
      <button class="secondary small" data-action="schedule">Schedule</button>
      <button class="secondary small" data-action="total_accept">Total Acceptance</button>
      <button class="secondary small" data-action="total_refuse">Total Refuse</button>
    `;
  }
  return "";
}

async function loadCommunicationList() {
  const screenings = await listCommunicationCandidates();
  const container = document.getElementById("communication-list");
  container.innerHTML = "";

  if (!screenings.length) {
    container.innerHTML = `<p class="muted small">No screened candidates yet.</p>`;
    return;
  }

  screenings.forEach((s) => {
    const row = document.createElement("div");
    row.className = "candidate-row";
    const statusBadge = s.decision
      ? `<span class="badge ${DECISION_CLASSES[s.decision]}">${DECISION_LABELS[s.decision]}</span>`
      : `<span class="badge ${s.category}">${s.verdict}</span>`;

    row.innerHTML = `
      <div>
        <strong>${s.candidate_name}</strong> — ${s.job_title} (score: ${s.score ?? "N/A"})
        <div class="row-sub">${s.justification || ""}</div>
      </div>
      <div class="row-actions">
        ${statusBadge}
        ${renderActions(s)}
      </div>
    `;

    const scheduleBtn = row.querySelector('[data-action="schedule"]');
    if (scheduleBtn) {
      scheduleBtn.addEventListener("click", () =>
        openScheduleModal(
          s.candidate_id,
          s.candidate_name,
          s.job_id,
          s.job_title,
        ),
      );
    }

    [
      "preselection_accept",
      "preselection_refuse",
      "total_accept",
      "total_refuse",
    ].forEach((action) => {
      const btn = row.querySelector(`[data-action="${action}"]`);
      if (!btn) return;
      btn.addEventListener("click", async () => {
        const confirmMsg =
          action === "total_accept"
            ? `Send acceptance email to ${s.candidate_name} and add them to Onboarding?`
            : `Send this decision email to ${s.candidate_name}?`;
        if (!confirm(confirmMsg)) return;
        btn.disabled = true;
        try {
          const result = await decideCommunication(s.id, action);
          showToast(
            result.email_sent
              ? "Decision saved, email sent"
              : "Decision saved, but the email could not be sent (check candidate email / SMTP setup)",
            result.email_sent ? "success" : "info",
          );
          await loadCommunicationList();
        } catch (err) {
          showToast(err.message, "error");
          btn.disabled = false;
        }
      });
    });

    container.appendChild(row);
  });
}
