import { apiFetch, apiFormUrlEncoded } from "./api.js";

export function markHired(candidateId, jobId) {
  return apiFormUrlEncoded(`/candidates/${candidateId}/hire`, {
    job_id: jobId,
  });
}

export function listOnboarding() {
  return apiFetch("/onboarding");
}
