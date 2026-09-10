import {
  proposeInterviewTimes,
  confirmInterview,
  listInterviews,
  listInterviewsToday,
} from "../services/scheduling.service.js";
import {
  openModal,
  closeModal,
  setupModalDismiss,
} from "../components/modal.js";
import { showToast } from "../components/toast.js";

const DISPLAY_TIMEZONE = "Africa/Tunis";

let scheduleCtx = null;

export async function renderSchedulingPage() {
  const view = document.getElementById("view-scheduling");
  view.innerHTML = `
    <h2>Scheduling window</h2>
    <p class="muted">Your confirmed interviews.</p>
    <div id="today-banner"></div>
    <div id="interviews-list"></div>
  `;
  await loadTodayInterviews();
  await loadInterviews();
}

async function loadTodayInterviews() {
  const bannerEl = document.getElementById("today-banner");
  const today = await listInterviewsToday();
  if (!today.length) {
    bannerEl.innerHTML = "";
    return;
  }
  bannerEl.innerHTML = `
    <div class="section" style="border-color:var(--color-accent); margin-bottom:12px;">
      <strong style="color:var(--color-accent);">Your interviews today</strong>
      ${today
        .map((i) => {
          const time = new Date(i.confirmed_time).toLocaleTimeString(
            undefined,
            {
              hour: "2-digit",
              minute: "2-digit",
              timeZone: DISPLAY_TIMEZONE,
            },
          );
          return `<div class="small" style="margin-top:6px;">${time} — ${i.candidate_name} (${i.job_title})</div>`;
        })
        .join("")}
    </div>
  `;
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
      <tr><th>Candidate</th><th>Job</th><th>Time (${DISPLAY_TIMEZONE})</th></tr>
      ${interviews
        .map((i) => {
          const readable = new Date(i.confirmed_time).toLocaleString(
            undefined,
            {
              dateStyle: "medium",
              timeStyle: "short",
              timeZone: DISPLAY_TIMEZONE,
            },
          );
          return `<tr><td>${i.candidate_name}</td><td>${i.job_title}</td><td>${readable}</td></tr>`;
        })
        .join("")}
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
    slotsEl.innerHTML = data.message
      ? `<p class="muted small">${data.message}</p>`
      : "";
    if (!slots.length) {
      slotsEl.innerHTML += `<p class="muted small">Enter a time manually below.</p>`;
    }
    slots.forEach((slot) => {
      const div = document.createElement("div");
      div.className = "slot-option";
      const readable = new Date(slot).toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: DISPLAY_TIMEZONE,
      });
      div.innerText = `${readable} (${DISPLAY_TIMEZONE})`;
      div.onclick = () => {
        document
          .querySelectorAll(".slot-option")
          .forEach((s) => s.classList.remove("selected"));
        div.classList.add("selected");
        document.getElementById("sched-custom").value = slot.slice(0, 16);
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
      let confirmedTime = document.getElementById("sched-custom").value.trim();
      if (!confirmedTime) {
        showToast("Pick or type a time first", "error");
        return;
      }
      if (confirmedTime.length === 16) confirmedTime += ":00";
      try {
        const result = await confirmInterview({
          candidateId: scheduleCtx.candidateId,
          jobId: scheduleCtx.jobId,
          confirmedTime,
        });
        closeModal(modal);
        if (result.calendar_link) {
          showToast("Interview scheduled and added to calendar", "success");
        } else {
          showToast(
            "Interview saved (calendar event failed — check manually)",
            "info",
          );
        }
      } catch (err) {
        showToast(err.message, "error");
      }
    });
}
