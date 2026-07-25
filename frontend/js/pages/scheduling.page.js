import {
  proposeInterviewTimes,
  confirmInterview,
  listInterviews,
} from "../services/scheduling.service.js";
import {
  openModal,
  closeModal,
  setupModalDismiss,
} from "../components/modal.js";
import { showToast } from "../components/toast.js";

let scheduleCtx = null;

export async function renderSchedulingPage() {
  const view = document.getElementById("view-scheduling");
  view.innerHTML = `
    <h2>Scheduling window</h2>
    <p class="muted">Your confirmed interviews.</p>
    <div id="interviews-list"></div>
  `;
  await loadInterviews();
}

async function loadInterviews() {
  const interviews = await listInterviews();
  const container = document.getElementById("interviews-list");
  if (!interviews.length) {
    container.innerHTML = `<p class="muted small">No interviews scheduled yet.</p>`;
    return;
  }
  container.innerHTML = `
    <table>
      <tr><th>Candidate</th><th>Job</th><th>Time</th></tr>
      ${interviews.map((i) => `<tr><td>${i.candidate_name}</td><td>${i.job_title}</td><td>${i.confirmed_time}</td></tr>`).join("")}
    </table>
  `;
}

export async function openScheduleModal(
  candidateId,
  candidateName,
  jobId,
  jobTitle,
) {
  scheduleCtx = { candidateId, candidateName, jobId, jobTitle };

  const modal = document.getElementById("schedule-modal");
  document.getElementById("sched-title").innerText =
    "Schedule: " + candidateName;
  document.getElementById("sched-custom").value = "";
  const slotsEl = document.getElementById("sched-slots");
  slotsEl.innerHTML = `<p class="muted small">Loading proposed times...</p>`;
  openModal(modal);

  try {
    const data = await proposeInterviewTimes(candidateName, jobTitle);
    const slots = data.proposed_slots || [];
    slotsEl.innerHTML = "";
    if (!slots.length) {
      slotsEl.innerHTML = `<p class="muted small">Could not generate proposed times. Enter one manually below.</p>`;
    }
    slots.forEach((slot) => {
      const div = document.createElement("div");
      div.className = "slot-option";
      div.innerText = slot;
      div.onclick = () => {
        document
          .querySelectorAll(".slot-option")
          .forEach((s) => s.classList.remove("selected"));
        div.classList.add("selected");
        document.getElementById("sched-custom").value = slot;
      };
      slotsEl.appendChild(div);
    });
  } catch (err) {
    slotsEl.innerHTML = `<p class="muted small">Error loading proposed times.</p>`;
  }
}

export function initScheduleModal() {
  const modal = document.getElementById("schedule-modal");
  setupModalDismiss(modal, document.getElementById("sched-cancel"));

  document
    .getElementById("sched-confirm")
    .addEventListener("click", async () => {
      const confirmedTime = document
        .getElementById("sched-custom")
        .value.trim();
      if (!confirmedTime) {
        showToast("Pick or type a time first", "error");
        return;
      }
      try {
        await confirmInterview({
          candidateId: scheduleCtx.candidateId,
          jobId: scheduleCtx.jobId,
          confirmedTime,
        });
        closeModal(modal);
        showToast("Interview scheduled for " + confirmedTime, "success");
      } catch (err) {
        showToast(err.message, "error");
      }
    });
}
