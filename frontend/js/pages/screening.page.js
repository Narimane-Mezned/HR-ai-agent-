import {
  listJobs,
  createJob,
  getJob,
  updateJob,
  deleteJob,
  getPendingCandidates,
} from "../services/jobs.service.js";
import {
  uploadCandidate,
  updateCandidate,
  deleteCandidate,
  getCandidateDetail,
  openResume,
} from "../services/candidates.service.js";
import {
  screenCandidates,
  getScreenings,
} from "../services/screenings.service.js";
import { renderJobList } from "../components/job-list.js";
import {
  openModal,
  closeModal,
  setupModalDismiss,
} from "../components/modal.js";
import { showToast } from "../components/toast.js";
import { openScheduleModal } from "./scheduling.page.js";

let activeJob = null;

export async function renderScreeningPage() {
  const view = document.getElementById("view-screening");
  view.innerHTML = `
    <div class="split">
      <div class="job-col">
        <div class="col-header">
          <h3>Jobs</h3>
          <button id="new-job-btn" class="primary small">+ New</button>
        </div>
        <div id="job-list"></div>
      </div>
      <div class="detail-col" id="job-detail" style="display:none;">
        <div class="col-header">
          <h2 id="job-title"></h2>
          <div>
            <button id="edit-job-btn" class="secondary small">Edit</button>
            <button id="delete-job-btn" class="secondary small">Delete</button>
          </div>
        </div>
        <p class="desc muted" id="job-desc"></p>
        <div class="section">
          <h4>Add candidate</h4>
          <form id="upload-form">
            <input id="candidate-name" placeholder="Candidate name" required>
            <input id="candidate-file" type="file" accept=".pdf" required>
            <button type="submit" class="primary">Upload &amp; Screen</button>
          </form>
        </div>
        <div class="section" id="pending-section">
          <h4>Pending applicants</h4>
          <div id="pending-list"></div>
        </div>
        <div class="section">
          <h4>Ranked candidates</h4>
          <div id="candidate-results"></div>
        </div>
      </div>
    </div>

    <div id="new-job-modal" class="modal-overlay" style="display:none;">
      <div class="modal">
        <h3 id="job-modal-title">New job</h3>
        <form id="job-form">
          <label>Title</label>
          <input id="nj-title" required>
          <label>Description</label>
          <textarea id="nj-desc" rows="3" required></textarea>
          <label>Requirements</label>
          <textarea id="nj-req" rows="2"></textarea>
          <div class="modal-actions">
            <button type="button" class="secondary" id="nj-cancel">Cancel</button>
            <button type="submit" class="primary" id="nj-submit">Create</button>
          </div>
        </form>
      </div>
    </div>

    <div id="edit-candidate-modal" class="modal-overlay" style="display:none;">
      <div class="modal">
        <h3>Update candidate CV</h3>
        <form id="edit-candidate-form">
          <input type="hidden" id="ec-id">
          <label>Name</label>
          <input id="ec-name" required>
          <label>New CV (PDF)</label>
          <input id="ec-file" type="file" accept=".pdf" required>
          <div class="modal-actions">
            <button type="button" class="secondary" id="ec-cancel">Cancel</button>
            <button type="submit" class="primary">Update &amp; Rescore</button>
          </div>
        </form>
      </div>
    </div>

    <div id="candidate-detail-modal" class="modal-overlay" style="display:none;">
      <div class="modal" style="width:520px; max-height:80vh; overflow-y:auto;">
        <h3 id="cd-name"></h3>
        <div id="cd-contact"></div>
        <div id="cd-answers"></div>
        <label style="margin-top:10px;">Full CV</label>
        <pre id="cd-cv" style="white-space:pre-wrap; font-size:12px; background:var(--color-bg); padding:10px; border-radius:var(--radius); max-height:250px; overflow-y:auto;"></pre>
        <div class="modal-actions">
          <button type="button" class="secondary" id="cd-open-resume" style="display:none;">Open CV (PDF)</button>
          <button type="button" class="secondary" id="cd-close">Close</button>
        </div>
      </div>
    </div>
  `;

  await loadJobs();

  const jobModal = document.getElementById("new-job-modal");
  setupModalDismiss(jobModal, document.getElementById("nj-cancel"));

  const candidateModal = document.getElementById("edit-candidate-modal");
  setupModalDismiss(candidateModal, document.getElementById("ec-cancel"));

  setupModalDismiss(
    document.getElementById("candidate-detail-modal"),
    document.getElementById("cd-close"),
  );

  document.getElementById("new-job-btn").addEventListener("click", () => {
    document.getElementById("job-modal-title").innerText = "New job";
    document.getElementById("nj-submit").innerText = "Create";
    document.getElementById("job-form").reset();
    document.getElementById("job-form").dataset.editing = "";
    openModal(jobModal);
  });

  document.getElementById("job-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("nj-title").value;
    const description = document.getElementById("nj-desc").value;
    const requirements = document.getElementById("nj-req").value;
    const editingId = e.target.dataset.editing;
    try {
      if (editingId) {
        await updateJob(editingId, { title, description, requirements });
        showToast("Job updated — rescoring candidates...", "info");
      } else {
        await createJob({ title, description, requirements });
        showToast("Job created", "success");
      }
      closeModal(jobModal);
      await loadJobs();
      if (editingId) await selectJob(Number(editingId));
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  document
    .getElementById("edit-candidate-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      const id = document.getElementById("ec-id").value;
      const name = document.getElementById("ec-name").value;
      const file = document.getElementById("ec-file").files[0];
      try {
        showToast("Updating and rescoring — this can take a moment...", "info");
        await updateCandidate(id, name, file);
        closeModal(candidateModal);
        await loadScreenings(activeJob.id);
        showToast("Candidate updated and rescored", "success");
      } catch (err) {
        showToast(err.message, "error");
      }
    });

  document
    .getElementById("upload-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!activeJob) return;
      const name = document.getElementById("candidate-name").value;
      const file = document.getElementById("candidate-file").files[0];
      try {
        const candidate = await uploadCandidate(name, file);
        showToast(
          "Screening candidate — this can take up to a minute...",
          "info",
        );
        await screenCandidates(activeJob.id, [candidate.id]);
        e.target.reset();
        await loadScreenings(activeJob.id);
        showToast("Screening complete", "success");
      } catch (err) {
        showToast(err.message, "error");
      }
    });
}

async function loadJobs() {
  const jobs = await listJobs();
  renderJobList(
    document.getElementById("job-list"),
    jobs,
    activeJob?.id,
    selectJob,
  );
}

async function selectJob(jobId) {
  activeJob = await getJob(jobId);
  const jobs = await listJobs();
  renderJobList(
    document.getElementById("job-list"),
    jobs,
    activeJob.id,
    selectJob,
  );

  document.getElementById("job-detail").style.display = "block";
  document.getElementById("job-title").innerText = activeJob.title;

  document.getElementById("edit-job-btn").onclick = () => {
    document.getElementById("job-modal-title").innerText = "Edit job";
    document.getElementById("nj-submit").innerText = "Save & Rescore";
    document.getElementById("nj-title").value = activeJob.title;
    document.getElementById("nj-desc").value = activeJob.description;
    document.getElementById("nj-req").value = activeJob.requirements || "";
    document.getElementById("job-form").dataset.editing = activeJob.id;
    openModal(document.getElementById("new-job-modal"));
  };

  document.getElementById("delete-job-btn").onclick = async () => {
    if (!confirm(`Delete "${activeJob.title}"? This cannot be undone.`)) return;
    await deleteJob(activeJob.id);
    activeJob = null;
    document.getElementById("job-detail").style.display = "none";
    showToast("Job deleted", "success");
    await loadJobs();
  };

  await loadScreenings(jobId);
  await loadPendingCandidates(jobId);
  document.getElementById("job-desc").innerHTML = `
  ${activeJob.description}
  <div style="margin-top:8px;">
    <small class="muted">Public application link: </small>
    <input readonly value="${window.location.origin}/static/apply.html?job_id=${activeJob.id}" style="width:auto; display:inline-block; font-size:12px;" onclick="this.select()">
  </div>
`;
}

async function openCandidateDetail(candidateId) {
  const detail = await getCandidateDetail(candidateId);
  document.getElementById("cd-name").innerText = detail.name;

  const contactParts = [];
  if (detail.email) contactParts.push(`Email: ${detail.email}`);
  if (detail.phone) contactParts.push(`Phone: ${detail.phone}`);
  const contactLine = contactParts.length
    ? `<p class="small">${contactParts.join(" · ")}</p>`
    : "";

  const links = [];
  if (detail.linkedin_url)
    links.push(`<a href="${detail.linkedin_url}" target="_blank">LinkedIn</a>`);
  if (detail.github_url)
    links.push(`<a href="${detail.github_url}" target="_blank">GitHub</a>`);
  const linksLine = links.length
    ? `<p class="small">${links.join(" · ")}</p>`
    : "";

  document.getElementById("cd-contact").innerHTML = contactLine + linksLine;

  const answersEl = document.getElementById("cd-answers");
  const entries = Object.entries(detail.prescreening_answers || {});
  answersEl.innerHTML = entries.length
    ? `<label>Pre-screening answers</label>` +
      entries
        .map(([q, a]) => `<p class="small"><strong>${q}</strong><br>${a}</p>`)
        .join("")
    : "";

  document.getElementById("cd-cv").innerText = detail.cv_text;

  const resumeBtn = document.getElementById("cd-open-resume");
  resumeBtn.style.display = detail.has_resume ? "inline-block" : "none";
  resumeBtn.onclick = () => openResume(candidateId);

  openModal(document.getElementById("candidate-detail-modal"));
}

async function loadScreenings(jobId) {
  const results = await getScreenings(jobId);
  results.sort((a, b) => (b.score || 0) - (a.score || 0));
  const container = document.getElementById("candidate-results");
  container.innerHTML = "";
  if (!results.length) {
    container.innerHTML = `<p class="muted small">No candidates screened for this job yet.</p>`;
    return;
  }
  results.forEach((r) => {
    const row = document.createElement("div");
    row.className = "candidate-row";
    row.innerHTML = `
      <div>
        <strong>${r.candidate_name}</strong> — score: ${r.score ?? "N/A"}
        <div class="row-sub">${r.justification || ""}</div>
      </div>
      <div class="row-actions">
        <span class="badge ${r.category}">${r.verdict}</span>
        <button class="secondary small" data-action="details">Details</button>
        <button class="secondary small" data-action="edit">Update CV</button>
        <button class="secondary small" data-action="delete">Delete</button>
        <button class="secondary small" data-action="schedule">Schedule</button>
        <button class="secondary small" data-action="hire">Mark Hired</button>
      </div>
    `;
    row
      .querySelector('[data-action="details"]')
      .addEventListener("click", () => openCandidateDetail(r.candidate_id));
    row
      .querySelector('[data-action="schedule"]')
      .addEventListener("click", () =>
        openScheduleModal(
          r.candidate_id,
          r.candidate_name,
          activeJob.id,
          activeJob.title,
        ),
      );
    row.querySelector('[data-action="edit"]').addEventListener("click", () => {
      document.getElementById("ec-id").value = r.candidate_id;
      document.getElementById("ec-name").value = r.candidate_name;
      document.getElementById("edit-candidate-form").reset();
      document.getElementById("ec-id").value = r.candidate_id;
      document.getElementById("ec-name").value = r.candidate_name;
      openModal(document.getElementById("edit-candidate-modal"));
    });
    row
      .querySelector('[data-action="delete"]')
      .addEventListener("click", async () => {
        if (!confirm(`Delete ${r.candidate_name}? This cannot be undone.`))
          return;
        await deleteCandidate(r.candidate_id);
        showToast("Candidate deleted", "success");
        await loadScreenings(activeJob.id);
      });
    container.appendChild(row);
    row
      .querySelector('[data-action="hire"]')
      .addEventListener("click", async () => {
        if (
          !confirm(
            `Mark ${r.candidate_name} as hired for ${activeJob.title}? This generates their onboarding checklist.`,
          )
        )
          return;
        showToast("Generating onboarding checklist...", "info");
        const { markHired } = await import("../services/onboarding.service.js");
        await markHired(r.candidate_id, activeJob.id);
        showToast("Candidate hired — check the Onboarding tab", "success");
      });
  });
}

async function loadPendingCandidates(jobId) {
  const pending = await getPendingCandidates(jobId);
  const container = document.getElementById("pending-list");
  container.innerHTML = "";
  if (!pending.length) {
    container.innerHTML = `<p class="muted small">No pending applicants.</p>`;
    return;
  }
  pending.forEach((c) => {
    const row = document.createElement("div");
    row.className = "candidate-row";
    row.innerHTML = `
      <div><strong>${c.name}</strong></div>
      <div class="row-actions">
        <button class="secondary small" data-action="details">Details</button>
        <button class="primary small" data-action="screen">Screen</button>
      </div>
    `;
    row
      .querySelector('[data-action="details"]')
      .addEventListener("click", () => openCandidateDetail(c.id));
    row
      .querySelector('[data-action="screen"]')
      .addEventListener("click", async () => {
        showToast("Screening candidate...", "info");
        await screenCandidates(jobId, [c.id]);
        await loadPendingCandidates(jobId);
        await loadScreenings(jobId);
        showToast("Screening complete", "success");
      });
    container.appendChild(row);
  });
}
