document.addEventListener('DOMContentLoaded', () => {
  const flashes = document.querySelectorAll('.flash');
  if (flashes.length) {
    setTimeout(() => {
      flashes.forEach(f => {
        f.style.transition = 'opacity 0.6s ease';
        f.style.opacity = '0';
      });
    }, 2600);
  }
});
