import { apiFetch, apiFormUrlEncoded } from "./api.js";

export function markHired(candidateId, jobId) {
  return apiFormUrlEncoded(`/candidates/${candidateId}/hire`, {
    job_id: jobId,
  });
}

export function listOnboarding() {
  return apiFetch("/onboarding");
}
export function toggleOnboardingItem(candidateId, listName, index) {
  return apiFormUrlEncoded(
    `/candidates/${candidateId}/onboarding/toggle-item`,
    {
      list_name: listName,
      index,
    },
  );
}
export function updateMentorName(candidateId, mentorName) {
  return apiFormUrlEncoded(
    `/candidates/${candidateId}/mentor`,
    { mentor_name: mentorName },
    "PUT",
  );
}
