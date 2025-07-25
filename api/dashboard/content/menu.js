document.querySelectorAll('.menu a').forEach(link => {
  link.addEventListener('click', () => {
    alert(`Navigating to ${link.getAttribute('href')}`);
  });
});