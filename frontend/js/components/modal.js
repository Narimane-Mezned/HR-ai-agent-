export function openModal(modalEl) {
  modalEl.style.display = "flex";
}
export function closeModal(modalEl) {
  modalEl.style.display = "none";
}

export function setupModalDismiss(modalEl, cancelBtnEl) {
  cancelBtnEl.addEventListener("click", () => closeModal(modalEl));
  modalEl.addEventListener("click", (e) => {
    if (e.target === modalEl) closeModal(modalEl);
  });
}
