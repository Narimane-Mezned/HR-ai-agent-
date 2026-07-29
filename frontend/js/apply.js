const jobId = new URLSearchParams(window.location.search).get("job_id");
let prescreeningQuestions = [];

async function loadJob() {
  if (!jobId) {
    document.getElementById("apply-job-title").innerText = "No job specified";
    document.getElementById("apply-form").style.display = "none";
    return;
  }

  try {
    const res = await fetch(`/public/jobs/${jobId}`);
    const job = await res.json();

    if (job.error) {
      document.getElementById("apply-job-title").innerText = "Job not found";
      document.getElementById("apply-form").style.display = "none";
      return;
    }

    document.getElementById("apply-job-title").innerText = job.title;
    document.getElementById("apply-job-desc").innerText = job.description;

    const qRes = await fetch(`/public/jobs/${jobId}/prescreening-questions`);
    const qData = await qRes.json();
    prescreeningQuestions = qData.questions || [];
    renderQuestions();
  } catch (err) {
    document.getElementById("apply-job-title").innerText = "Could not load job";
  }
}

function renderQuestions() {
  if (!prescreeningQuestions.length) return;
  const container = document.getElementById("apply-questions");
  container.innerHTML = `<label style="margin-top:10px;">A few quick questions</label>`;
  prescreeningQuestions.forEach((q, i) => {
    container.innerHTML += `
      <label class="small" style="margin-top:8px;">${q}</label>
      <input class="prescreen-answer" data-question="${q}" required>
    `;
  });
}

document.getElementById("apply-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = document.getElementById("apply-name").value;
  const file = document.getElementById("apply-file").files[0];
  const statusEl = document.getElementById("apply-status");
  const submitBtn = e.target.querySelector("button");

  const answers = {};
  document.querySelectorAll(".prescreen-answer").forEach((input) => {
    answers[input.dataset.question] = input.value;
  });

  const formData = new FormData();
  formData.append("name", name);
  formData.append("file", file);
  formData.append("prescreening_answers", JSON.stringify(answers));
  formData.append("phone", document.getElementById("apply-phone").value);
  formData.append("github_url", document.getElementById("apply-github").value);

  statusEl.style.color = "";
  statusEl.innerText = "Submitting...";
  submitBtn.disabled = true;

  try {
    const res = await fetch(`/public/jobs/${jobId}/apply`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();

    if (data.candidate_id) {
      document.getElementById("apply-form").style.display = "none";
      statusEl.style.color = "var(--color-success-text)";
      statusEl.innerText =
        "Application received — thank you! We'll be in touch.";
    } else {
      statusEl.style.color = "var(--color-danger-text)";
      statusEl.innerText =
        data.error || "Something went wrong. Please try again.";
      submitBtn.disabled = false;
    }
  } catch (err) {
    statusEl.style.color = "var(--color-danger-text)";
    statusEl.innerText = "Network error. Please try again.";
    submitBtn.disabled = false;
  }
});

loadJob();
