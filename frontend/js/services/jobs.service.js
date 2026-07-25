import { apiFetch, apiFormUrlEncoded } from "./api.js";

export function listJobs() {
  return apiFetch("/jobs");
}
export function getJob(jobId) {
  return apiFetch(`/jobs/${jobId}`);
}
export function createJob({ title, description, requirements }) {
  return apiFormUrlEncoded("/jobs", { title, description, requirements });
}
export function updateJob(jobId, fields) {
  return apiFormUrlEncoded(`/jobs/${jobId}`, fields, "PUT");
}
export function deleteJob(jobId) {
  return apiFetch(`/jobs/${jobId}`, { method: "DELETE" });
}
export function getPendingCandidates(jobId) {
  return apiFetch(`/jobs/${jobId}/pending-candidates`);
}
