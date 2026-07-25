export function renderJobList(container, jobs, activeJobId, onSelect) {
  container.innerHTML = "";
  if (!jobs.length) {
    container.innerHTML = `<p class="muted small">No jobs yet.</p>`;
    return;
  }
  jobs.forEach((job) => {
    const div = document.createElement("div");
    div.className = "job-item" + (job.id === activeJobId ? " active" : "");
    div.innerText = job.title;
    div.onclick = () => onSelect(job.id);
    container.appendChild(div);
  });
}
