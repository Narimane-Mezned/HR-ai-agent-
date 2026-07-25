import { apiFetch, apiForm, apiFormPut } from "./api.js";

export function listCandidates() {
  return apiFetch("/candidates");
}

export function uploadCandidate(name, file) {
  const formData = new FormData();
  formData.append("name", name);
  formData.append("file", file);
  return apiForm("/candidates", formData);
}

export function updateCandidate(candidateId, name, file) {
  const formData = new FormData();
  formData.append("name", name);
  formData.append("file", file);
  return apiFormPut(`/candidates/${candidateId}`, formData);
}

export function deleteCandidate(candidateId) {
  return apiFetch(`/candidates/${candidateId}`, { method: "DELETE" });
}
