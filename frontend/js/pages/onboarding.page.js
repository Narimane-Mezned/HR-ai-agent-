import { listOnboarding } from "../services/onboarding.service.js";

export async function renderOnboardingPage() {
  const view = document.getElementById("view-onboarding");
  view.innerHTML = `
    <h2>Onboarding</h2>
    <p class="muted">Personalized checklists for hired candidates.</p>
    <div id="onboarding-list"></div>
  `;

  const hired = await listOnboarding();
  const container = document.getElementById("onboarding-list");
  if (!hired.length) {
    container.innerHTML = `<p class="muted small">No candidates hired yet.</p>`;
    return;
  }

  hired.forEach((h) => {
    const section = document.createElement("div");
    section.className = "section";
    section.innerHTML = `
      <h4>${h.candidate_name} — ${h.job_title}</h4>
      <p class="small muted">${h.welcome_message}</p>
      <ul>${h.checklist.map((item) => `<li class="small">${item}</li>`).join("")}</ul>
    `;
    container.appendChild(section);
  });
}
