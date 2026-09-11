import {
  listOnboarding,
  toggleOnboardingItem,
  updateMentorName,
} from "../services/onboarding.service.js";
import { showToast } from "../components/toast.js";

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

export async function renderOnboardingPage() {
  const view = document.getElementById("view-onboarding");
  view.innerHTML = `
    <h2>Onboarding</h2>
    <p class="muted">Personalized plans for hired candidates.</p>
    <div id="onboarding-list"></div>
  `;

  await loadOnboarding();
}

function renderChecklist(items, listName) {
  return `
    <table class="onboarding-checklist" data-list="${listName}">
      ${items
        .map(
          (item, i) => `
        <tr>
          <td class="${item.done ? "checklist-done" : ""}">${escapeHtml(item.text)}</td>
          <td style="width:40px; text-align:center;">
            <input type="checkbox" data-index="${i}" ${item.done ? "checked" : ""}>
          </td>
        </tr>`,
        )
        .join("")}
    </table>
  `;
}

async function loadOnboarding() {
  const hired = await listOnboarding();
  const container = document.getElementById("onboarding-list");
  container.innerHTML = "";
  if (!hired.length) {
    container.innerHTML = `<p class="muted small">No candidates hired yet.</p>`;
    return;
  }

  hired.forEach((h) => {
    const section = document.createElement("div");
    section.className = "section";
    section.innerHTML = `
      <h3>${escapeHtml(h.candidate_name)} — ${escapeHtml(h.job_title)}</h3>
      <p class="small muted">${escapeHtml(h.welcome_message)}</p>

      ${
        h.first_day_agenda.length
          ? `<div class="onboarding-section-title">First day agenda</div>
             <ul>${h.first_day_agenda.map((item) => `<li class="small">${escapeHtml(item)}</li>`).join("")}</ul>`
          : ""
      }

      ${
        h.access_checklist.length
          ? `<div class="onboarding-section-title" style="margin-top:14px;">Access & tools</div>
             ${renderChecklist(h.access_checklist, "access_checklist")}`
          : ""
      }

      <div class="onboarding-section-title" style="margin-top:14px;">First two weeks</div>
      ${renderChecklist(h.checklist, "checklist")}

      <div class="onboarding-section-title" style="margin-top:14px;">Mentor</div>
      <p class="small muted" style="margin-bottom:6px;">Assigned by the technical recruiter</p>
      <div style="display:flex; gap:8px;">
        <input class="mentor-input" placeholder="Mentor name" value="${escapeHtml(h.mentor_name)}" style="margin-bottom:0;">
        <button class="secondary small mentor-save">Save</button>
      </div>
    `;

    section.querySelectorAll(".onboarding-checklist").forEach((listEl) => {
      const listName = listEl.dataset.list;
      listEl.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
        checkbox.addEventListener("change", async () => {
          const index = Number(checkbox.dataset.index);
          checkbox.disabled = true;
          try {
            await toggleOnboardingItem(h.candidate_id, listName, index);
            await loadOnboarding();
          } catch (err) {
            showToast(err.message, "error");
            checkbox.disabled = false;
          }
        });
      });
    });

    section
      .querySelector(".mentor-save")
      .addEventListener("click", async () => {
        const mentorName = section.querySelector(".mentor-input").value.trim();
        try {
          await updateMentorName(h.candidate_id, mentorName);
          showToast("Mentor saved", "success");
        } catch (err) {
          showToast(err.message, "error");
        }
      });

    container.appendChild(section);
  });
}
