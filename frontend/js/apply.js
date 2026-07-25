const jobId = new URLSearchParams(window.location.search).get("job_id");

async function loadJob() {
  const res = await fetch(`/public/jobs/${jobId}`);
  const job = await res.json();
  if (job.error) {
    document.getElementById("apply-job-title").innerText = "Job not found";
    return;
  }
  document.getElementById("apply-job-title").innerText = job.title;
  document.getElementById("apply-job-desc").innerText = job.description;
}

document.getElementById("apply-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("apply-name").value;
  const file = document.getElementById("apply-file").files[0];
  const formData = new FormData();
  formData.append("name", name);
  formData.append("file", file);

  const statusEl = document.getElementById("apply-status");
  statusEl.style.color = "inherit";
  statusEl.innerText = "Submitting...";

  const res = await fetch(`/public/jobs/${jobId}/apply`, {
    method: "POST",
    body: formData,
  });
  const data = await res.json();
  if (data.candidate_id) {
    document.getElementById("apply-form").style.display = "none";
    statusEl.style.color = "green";
    statusEl.innerText = "Application received — thank you!";
  } else {
    statusEl.innerText = data.error || "Something went wrong.";
  }
});

loadJob();
