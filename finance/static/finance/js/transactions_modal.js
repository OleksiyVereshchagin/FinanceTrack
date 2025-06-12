function showDeleteModal(title, amount, deleteUrl, csrfToken) {
  console.log("showDeleteModal викликана");

  const modal = document.getElementById('deleteModal');
  const nameEl = document.getElementById('transactionName');
  const amountEl = document.getElementById('transactionAmount');
  const form = document.getElementById('deleteForm');

  if (!modal || !nameEl || !amountEl || !form) {
    console.error("Елемент модального вікна не знайдено!");
    return;
  }

  nameEl.innerText = title;
  amountEl.innerText = amount;
  form.action = deleteUrl;

  const csrfInput = form.querySelector('input[name=csrfmiddlewaretoken]');
  if (csrfInput) {
    csrfInput.value = csrfToken;
  }

  modal.style.display = 'flex';
}

function hideDeleteModal() {
  const modal = document.getElementById('deleteModal');
  if (modal) {
    modal.style.display = 'none';
  }
}