import { apiFetch, apiFormUrlEncoded } from "./api.js";

export function listCommunicationCandidates() {
  return apiFetch("/communication/candidates");
}

export function decideCommunication(screeningId, action) {
  return apiFormUrlEncoded(`/communication/screenings/${screeningId}/decide`, {
    action,
  });
}
