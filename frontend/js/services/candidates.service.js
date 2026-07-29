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
export function getCandidateDetail(candidateId) {
  return apiFetch(`/candidates/${candidateId}/detail`);
}
export async function openResume(candidateId) {
  const token = localStorage.getItem("token");
  const res = await fetch(`/candidates/${candidateId}/resume`, {
    headers: { Authorization: "Bearer " + token },
  });
  if (!res.ok) throw new Error("Resume not available");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank");
}
