import { apiFetch } from "./api.js";

export function getMatchesForCandidate(candidateId) {
  return apiFetch(`/candidates/${candidateId}/matches`);
}
