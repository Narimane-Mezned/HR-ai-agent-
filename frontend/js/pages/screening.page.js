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
  downloadScreeningsCsv,
} from "../services/screenings.service.js";
import { renderJobList } from "../components/job-list.js";
import {
  openModal,
  closeModal,
  setupModalDismiss,
} from "../components/modal.js";
import { showToast } from "../components/toast.js";

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
          <div class="col-header">
            <h4>Ranked candidates</h4>
            <button id="export-csv-btn" class="secondary small">Export CSV</button>
          </div>
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
          <label>Location</label>
          <select id="nj-location">
            <option value="">Not specified</option>
            <option value="Tunis">Tunis</option>
            <option value="Sousse">Sousse</option>
            <option value="Sfax">Sfax</option>
            <option value="Monastir">Monastir</option>
            <option value="Ariana">Ariana</option>
            <option value="Remote">Remote</option>
          </select>
          <label>Remote policy</label>
          <select id="nj-remote">
            <option value="">Not specified</option>
            <option value="On-site">On-site</option>
            <option value="Hybrid">Hybrid</option>
            <option value="Remote">Remote</option>
          </select>
          <label>Experience level</label>
          <select id="nj-experience">
            <option value="">Not specified</option>
            <option value="Junior">Junior</option>
            <option value="Mid">Mid</option>
            <option value="Senior">Senior</option>
          </select>
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
      <div class="modal" style="width:800px; max-width:90vw; max-height:80vh; overflow-y:auto;">
        <h3 id="cd-name"></h3>
        <div id="cd-screening"></div>
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

  document
    .getElementById("export-csv-btn")
    .addEventListener("click", async () => {
      if (!activeJob) return;
      try {
        await downloadScreeningsCsv(activeJob.id, activeJob.title);
      } catch (err) {
        showToast(err.message, "error");
      }
    });

  document.getElementById("job-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("nj-title").value;
    const description = document.getElementById("nj-desc").value;
    const requirements = document.getElementById("nj-req").value;
    const location = document.getElementById("nj-location").value;
    const remote_policy = document.getElementById("nj-remote").value;
    const experience_level = document.getElementById("nj-experience").value;
    const editingId = e.target.dataset.editing;
    try {
      if (editingId) {
        await updateJob(editingId, {
          title,
          description,
          requirements,
          location,
          remote_policy,
          experience_level,
        });
        showToast("Job updated — rescoring candidates...", "info");
      } else {
        await createJob({
          title,
          description,
          requirements,
          location,
          remote_policy,
          experience_level,
        });
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
      const submitBtn = e.target.querySelector('button[type="submit"]');
      if (submitBtn.disabled) return;
      submitBtn.disabled = true;
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
      } finally {
        submitBtn.disabled = false;
      }
    });

  document
    .getElementById("upload-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!activeJob) return;
      const submitBtn = e.target.querySelector('button[type="submit"]');
      if (submitBtn.disabled) return;
      submitBtn.disabled = true;
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
      } finally {
        submitBtn.disabled = false;
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
    document.getElementById("nj-location").value = activeJob.location || "";
    document.getElementById("nj-remote").value = activeJob.remote_policy || "";
    document.getElementById("nj-experience").value =
      activeJob.experience_level || "";
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

function normalizeUrl(url) {
  if (!url) return url;
  return /^https?:\/\//i.test(url) ? url : `https://${url}`;
}

async function openCandidateDetail(candidateId, screening = null) {
  const detail = await getCandidateDetail(candidateId);
  document.getElementById("cd-name").innerText = detail.name;

  const screeningEl = document.getElementById("cd-screening");
  if (screening) {
    let languages = [];
    try {
      languages = JSON.parse(screening.languages || "[]");
    } catch {
      languages = [];
    }
    screeningEl.innerHTML = `
      <p class="small"><strong>Score:</strong> ${screening.score ?? "N/A"} — <span class="badge ${screening.category}">${screening.verdict}</span></p>
      ${screening.education ? `<p class="small"><strong>Education:</strong> ${screening.education}</p>` : ""}
      ${languages.length ? `<p class="small"><strong>Languages:</strong> ${languages.join(", ")}</p>` : ""}
      ${screening.location ? `<p class="small"><strong>Location:</strong> ${screening.location}</p>` : ""}
      ${screening.confidence_level ? `<p class="small"><strong>Confidence:</strong> ${screening.confidence_level}${screening.confidence_reasoning ? ` — ${screening.confidence_reasoning}` : ""}</p>` : ""}
    `;
  } else {
    screeningEl.innerHTML = "";
  }

  const contactParts = [];
  if (detail.email) contactParts.push(`Email: ${detail.email}`);
  if (detail.phone) contactParts.push(`Phone: ${detail.phone}`);
  const contactLine = contactParts.length
    ? `<p class="small">${contactParts.join(" · ")}</p>`
    : "";

  const links = [];
  if (detail.linkedin_url)
    links.push(
      `<a href="${normalizeUrl(detail.linkedin_url)}" target="_blank">LinkedIn</a>`,
    );
  if (detail.github_url)
    links.push(
      `<a href="${normalizeUrl(detail.github_url)}" target="_blank">GitHub</a>`,
    );
  const linksLine = links.length
    ? `<p class="small">${links.join(" · ")}</p>`
    : "";

  document.getElementById("cd-contact").innerHTML = contactLine + linksLine;

  const answersEl = document.getElementById("cd-answers");
  const entries = Object.entries(detail.prescreening_answers || {});
  const flags = detail.prescreening_flags;
  const flagsHtml =
    flags && flags.has_concerns
      ? `<div class="section" style="border-color:var(--color-danger-text); margin-bottom:8px;">
         <strong style="color:var(--color-danger-text);">⚠ Pre-screening concerns</strong>
         <ul style="margin:6px 0 0 18px; font-size:13px;">
           ${flags.concerns.map((c) => `<li>${c}</li>`).join("")}
         </ul>
       </div>`
      : "";
  answersEl.innerHTML =
    flagsHtml +
    (entries.length
      ? `<label>Pre-screening answers</label>` +
        entries
          .map(([q, a]) => `<p class="small"><strong>${q}</strong><br>${a}</p>`)
          .join("")
      : "");

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
      </div>
    `;
    row
      .querySelector('[data-action="details"]')
      .addEventListener("click", () => openCandidateDetail(r.candidate_id, r));
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
    let flags = null;
    try {
      flags = c.prescreening_flags ? JSON.parse(c.prescreening_flags) : null;
    } catch {
      flags = null;
    }
    const flagBadge =
      flags && flags.has_concerns
        ? `<span class="badge not_suitable" title="${flags.concerns.join(" | ").replace(/"/g, "&quot;")}">⚠ Flagged</span>`
        : "";
    row.innerHTML = `
      <div><strong>${c.name}</strong> ${flagBadge}</div>
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
      .addEventListener("click", async (e) => {
        const btn = e.currentTarget;
        if (btn.disabled) return;
        btn.disabled = true;
        try {
          showToast("Screening candidate...", "info");
          await screenCandidates(jobId, [c.id]);
          await loadPendingCandidates(jobId);
          await loadScreenings(jobId);
          showToast("Screening complete", "success");
        } finally {
          btn.disabled = false;
        }
      });
    container.appendChild(row);
  });
}
