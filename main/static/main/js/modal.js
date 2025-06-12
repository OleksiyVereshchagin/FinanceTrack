document.addEventListener("DOMContentLoaded", function () {
  const openBtn = document.getElementById("open-create-modal");
  const modalContainer = document.getElementById("modal-container");

  if (openBtn && modalContainer) {
    openBtn.addEventListener("click", function (e) {
      e.preventDefault();
      fetch(this.href)
        .then((response) => response.text())
        .then((html) => {
          modalContainer.innerHTML = html;
          modalContainer.style.display = "block";

          // Додаємо подію для кнопки закриття
          const closeBtn = document.getElementById("close-modal");
          if (closeBtn) {
            closeBtn.addEventListener("click", () => {
              modalContainer.style.display = "none";
              modalContainer.innerHTML = "";
            });
          }
        });
    });
  }
});

// static/main/js/modal.js
function showDeleteModal(title, text, url) {
  document.getElementById('modalDeleteTitle').textContent = title;
  document.getElementById('modalDeleteText').innerHTML = text;
  document.getElementById('deleteForm').action = url;
  document.getElementById('deleteModal').style.display = 'flex';
}

function closeModal() {
  document.getElementById('deleteModal').style.display = 'none';
}


