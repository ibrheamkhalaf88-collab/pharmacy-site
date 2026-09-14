/**
 * Cart module — السلة
 * يحفظ المنتجات ويحسب المجموع
 */
const Cart = {
  _items: [],

  init() {
    this._items = JSON.parse(localStorage.getItem('salaq_cart') || '[]');
  },

  save() {
    localStorage.setItem('salaq_cart', JSON.stringify(this._items));
  },

  add(product) {
    const existing = this._items.find(i => i.id === product.id);
    if (existing) {
      existing.qty += 1;
    } else {
      this._items.push({ ...product, qty: 1 });
    }
    this.save();
    this.render();
  },

  remove(id) {
    this._items = this._items.filter(i => i.id !== id);
    this.save();
    this.render();
  },

  clear() {
    this._items = [];
    this.save();
    this.render();
  },

  getItems() {
    return this._items;
  },

  getTotal() {
    return this._items.reduce((sum, item) => sum + item.price * item.qty, 0);
  },

  getItemCount() {
    return this._items.reduce((sum, item) => sum + item.qty, 0);
  },

  isEmpty() {
    return this._items.length === 0;
  },

  render() {
    const bar = document.getElementById('cartBar');
    const itemsEl = document.getElementById('cartItems');
    const totalEl = document.getElementById('cartTotal');
    const countEl = document.getElementById('cartCount');
    const checkoutBtn = document.getElementById('checkoutBtn');
    const clearBtn = document.getElementById('clearCart');

    if (this.isEmpty()) {
      itemsEl.innerHTML = '<span style="color:#8C8C84;font-size:13px">السلة فارغة — أضف منتجاً للطلب</span>';
      checkoutBtn.style.display = 'none';
      clearBtn.style.display = 'none';
      return;
    }

    checkoutBtn.style.display = 'inline-flex';
    clearBtn.style.display = 'inline-flex';

    itemsEl.innerHTML = this._items.map(item => `
      <div class="cart-item" data-id="${item.id}">
        <svg class="cart-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/></svg>
        <span class="cart-item-name">${item.name}</span>
        <span class="cart-item-qty">×${item.qty}</span>
        <button class="cart-item-remove" data-id="${item.id}" title="إزالة">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>
    `).join('');

    totalEl.textContent = this.getTotal().toFixed(2);
    countEl.textContent = this.getItemCount();
  },

  // بالشراكات التالية بعد تحميل DOM
  bindEvents() {
    document.getElementById('cartItems').addEventListener('click', (e) => {
      const btn = e.target.closest('.cart-item-remove');
      if (btn) this.remove(parseInt(btn.dataset.id));
    });

    document.getElementById('clearCart').addEventListener('click', () => {
      if (confirm('مسح كل المنتجات من السلة؟')) {
        this.clear();
      }
    });
  }
};

// عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', () => {
  Cart.init();
  Cart.bindEvents();
  Cart.render();
});
