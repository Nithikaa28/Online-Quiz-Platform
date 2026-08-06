// FoodHub frontend interactions: cart, filters, theme, and responsive nav.
document.addEventListener('DOMContentLoaded', () => {
  const cartKey = 'foodhub_cart';

  const readCart = () => JSON.parse(localStorage.getItem(cartKey) || '[]');
  const saveCart = (cart) => localStorage.setItem(cartKey, JSON.stringify(cart));

  const addToCart = (item) => {
    const cart = readCart();
    const existing = cart.find((x) => x.id === item.id);
    if (existing) {
      existing.quantity += 1;
    } else {
      cart.push({ ...item, quantity: 1 });
    }
    saveCart(cart);
    alert(`${item.name} added to cart`);
  };

  document.querySelectorAll('.add-cart-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const card = e.target.closest('.menu-item');
      addToCart({
        id: card.dataset.id,
        name: card.dataset.name,
        price: Number(card.dataset.price),
        image: card.dataset.image
      });
    });
  });

  const renderCart = (targetId, totalId) => {
    const container = document.getElementById(targetId);
    const totalEl = document.getElementById(totalId);
    if (!container || !totalEl) return;

    const cart = readCart();
    if (!cart.length) {
      container.innerHTML = '<p>Your cart is empty. Add dishes from the menu.</p>';
      totalEl.textContent = '0';
      return;
    }

    container.innerHTML = cart.map((item) => `
      <article class="cart-item">
        <img src="${item.image}" alt="${item.name}">
        <div>
          <h3>${item.name}</h3>
          <p>₹${item.price}</p>
          <div class="qty-controls">
            <button data-action="decrease" data-id="${item.id}">-</button>
            <span>${item.quantity}</span>
            <button data-action="increase" data-id="${item.id}">+</button>
            <button data-action="remove" data-id="${item.id}">🗑</button>
          </div>
        </div>
        <strong>₹${item.price * item.quantity}</strong>
      </article>
    `).join('');

    const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
    totalEl.textContent = String(total);

    container.querySelectorAll('button[data-action]').forEach((button) => {
      button.addEventListener('click', () => {
        const id = button.dataset.id;
        const action = button.dataset.action;
        const nextCart = readCart().map((x) => ({ ...x }));
        const index = nextCart.findIndex((x) => x.id === id);
        if (index === -1) return;

        if (action === 'increase') nextCart[index].quantity += 1;
        if (action === 'decrease') nextCart[index].quantity -= 1;
        if (action === 'remove' || nextCart[index].quantity <= 0) nextCart.splice(index, 1);

        saveCart(nextCart);
        renderCart(targetId, totalId);
      });
    });
  };

  renderCart('cartContainer', 'cartTotal');
  renderCart('checkoutSummary', 'checkoutTotal');

  const checkoutForm = document.getElementById('checkoutForm');
  const orderSuccess = document.getElementById('orderSuccess');
  if (checkoutForm && orderSuccess) {
    checkoutForm.addEventListener('submit', (e) => {
      e.preventDefault();
      orderSuccess.textContent = '✅ Order placed successfully! Your food is on the way.';
      saveCart([]);
      renderCart('checkoutSummary', 'checkoutTotal');
      checkoutForm.reset();
    });
  }

  document.querySelectorAll('.filter-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.dataset.filter;
      document.querySelectorAll('.menu-item').forEach((item) => {
        item.style.display = filter === 'all' || item.dataset.category === filter ? 'block' : 'none';
      });
    });
  });

  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    const savedTheme = localStorage.getItem('foodhub_theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    themeToggle.textContent = savedTheme === 'dark' ? '☀️' : '🌙';

    themeToggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const next = current === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('foodhub_theme', next);
      themeToggle.textContent = next === 'dark' ? '☀️' : '🌙';
    });
  }

  const mobileToggle = document.getElementById('mobileToggle');
  const navLinks = document.getElementById('navLinks');
  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
    });
  }
});
