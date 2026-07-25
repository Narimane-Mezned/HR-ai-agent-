import { apiFetch, apiFormUrlEncoded } from "./api.js";

export function screenCandidates(jobId, candidateIds) {
  return apiFormUrlEncoded(`/jobs/${jobId}/screen`, {
    candidate_ids: candidateIds.join(","),
  });
}

export function getScreenings(jobId) {
  return apiFetch(`/jobs/${jobId}/screenings`);
}
