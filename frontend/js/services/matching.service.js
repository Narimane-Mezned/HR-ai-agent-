import { apiFetch } from "./api.js";

export function getMatchesForCandidate(candidateId, filters = {}) {
  const params = new URLSearchParams();
  if (filters.location) params.set("location", filters.location);
  if (filters.remote_policy) params.set("remote_policy", filters.remote_policy);
  if (filters.experience_level)
    params.set("experience_level", filters.experience_level);
  const qs = params.toString();
  return apiFetch(`/candidates/${candidateId}/matches${qs ? `?${qs}` : ""}`);
}
