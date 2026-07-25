import { apiFetch, apiFormUrlEncoded } from "./api.js";

export function proposeInterviewTimes(candidateName, jobTitle) {
  return apiFormUrlEncoded("/screenings/propose-times", {
    candidate_name: candidateName,
    job_title: jobTitle,
  });
}

export function confirmInterview({ candidateId, jobId, confirmedTime }) {
  return apiFormUrlEncoded("/interviews", {
    candidate_id: candidateId,
    job_id: jobId,
    confirmed_time: confirmedTime,
  });
}

export function listInterviews() {
  return apiFetch("/interviews");
}
