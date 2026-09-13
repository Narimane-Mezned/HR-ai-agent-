import { apiFetch, apiFormUrlEncoded } from "./api.js";

export function screenCandidates(jobId, candidateIds) {
  return apiFormUrlEncoded(`/jobs/${jobId}/screen`, {
    candidate_ids: candidateIds.join(","),
  });
}

export function getScreenings(jobId) {
  return apiFetch(`/jobs/${jobId}/screenings`);
}

export async function downloadScreeningsCsv(jobId, jobTitle) {
  const token = localStorage.getItem("token");
  const res = await fetch(`/jobs/${jobId}/screenings/export`, {
    headers: token ? { Authorization: "Bearer " + token } : {},
  });
  if (!res.ok) {
    throw new Error("Failed to export candidates.");
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${(jobTitle || "candidates").replace(/\s+/g, "_")}_candidates.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
