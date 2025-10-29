// Dropdown toggle for small screens
document.querySelectorAll('.drop-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    btn.nextElementSibling.classList.toggle('show');
  });
});

// Try Now button click
document.getElementById('tryBtn').addEventListener('click', () => {
  alert('Opening Screener AI Chat...');
});

// Optional: close dropdowns when clicking outside
window.addEventListener('click', (e) => {
  document.querySelectorAll('.dropdown-content').forEach(menu => {
    if (!menu.parentElement.contains(e.target)) {
      menu.classList.remove('show');
    }
  });
});
