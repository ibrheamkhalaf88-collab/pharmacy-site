/**
 * Cart module — السلة
 * يحفظ المنتجات ويحسب المجموع، ويرسل الطلب عبر POST /api/orders
 * ثم يفتح رابط الواتساب الذي يولّده الخادم (الطلب يُسجّل في DB).
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

  escHtml(v) {
    return String(v ?? '').replace(/[&<>"']/g, c => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
  },

  render() {
    const itemsEl = document.getElementById('cartItems');
    const totalEl = document.getElementById('cartTotal');
    const countEl = document.getElementById('cartCount');
    const checkoutBtn = document.getElementById('checkoutBtn');
    const clearBtn = document.getElementById('clearCart');
    if (!itemsEl) return;

    if (this.isEmpty()) {
      itemsEl.innerHTML = '<span style="color:#8C8C84;font-size:13px">السلة فارغة — أضف منتجاً للطلب</span>';
      if (checkoutBtn) checkoutBtn.style.display = 'none';
      if (clearBtn) clearBtn.style.display = 'none';
      return;
    }

    if (checkoutBtn) checkoutBtn.style.display = 'inline-flex';
    if (clearBtn) clearBtn.style.display = 'inline-flex';

    itemsEl.innerHTML = this._items.map(item => `
      <div class="cart-item" data-id="${this.escHtml(item.id)}">
        <svg class="cart-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/></svg>
        <span class="cart-item-name">${this.escHtml(item.name)}</span>
        <span class="cart-item-qty">&times;${item.qty}</span>
        <button class="cart-item-remove" data-id="${this.escHtml(item.id)}" title="إزالة">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>
    `).join('');

    if (totalEl) totalEl.textContent = this.getTotal().toFixed(2);
    if (countEl) countEl.textContent = this.getItemCount();
  },

  // ── مودال إتمام الطلب ──
  getModal() {
    return document.getElementById('checkout-modal');
  },

  openCheckout() {
    const modal = this.getModal();
    if (!modal) {
      if (window.showToast) window.showToast('تعذر فتح نموذج الطلب');
      return;
    }
    if (this.isEmpty()) {
      if (window.showToast) window.showToast('السلة فارغة — أضف منتجاً أولاً');
      return;
    }
    const totalEl = document.getElementById('co-total');
    if (totalEl) totalEl.textContent = this.getTotal().toFixed(2) + ' شيكل';
    const err = document.getElementById('checkout-error');
    if (err) { err.classList.add('hidden'); err.classList.remove('flex'); }
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    const nameEl = document.getElementById('co-name');
    if (nameEl) nameEl.focus();
  },

  closeCheckout() {
    const modal = this.getModal();
    if (!modal) return;
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  },

  setModalError(msg) {
    const err = document.getElementById('checkout-error');
    const msgEl = document.getElementById('checkout-error-msg');
    if (!err || !msgEl) return;
    msgEl.textContent = msg;
    err.classList.remove('hidden');
    err.classList.add('flex');
  },

  async submitCheckout(e) {
    if (e && e.preventDefault) e.preventDefault();
    const name = String(document.getElementById('co-name').value || '').trim();
    const phone = String(document.getElementById('co-phone').value || '').trim();
    const notes = String(document.getElementById('co-notes').value || '').trim();
    const digits = phone.replace(/\D/g, '');

    if (name.length < 2) { this.setModalError('أدخل الاسم الكامل من فضلك'); return; }
    if (digits.length < 9) { this.setModalError('أدخل رقم جوال صالح مثل 0591234567'); return; }

    const submitBtn = document.getElementById('checkoutSubmit');
    const originalLabel = submitBtn ? submitBtn.innerHTML : '';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="material-symbols-outlined text-lg animate-spin">sync</span><span>جاري إرسال الطلب...</span>';
    }

    try {
      const res = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_name: name,
          customer_phone: phone,
          notes: notes,
          items: this._items.map(i => ({ product_id: i.id, quantity: i.qty })),
        }),
      });

      if (!res.ok) {
        let detail = 'حدث خطأ أثناء إرسال الطلب — حاول مرة أخرى';
        try {
          const errData = await res.json();
          if (errData && errData.detail) detail = errData.detail;
        } catch (_) { /* ignore parse errors */ }
        this.setModalError(detail);
        return;
      }

      const data = await res.json();
      this.closeCheckout();
      const url = (data && data.whatsapp_url) || '';
      if (url) window.open(url, '_blank', 'noopener');
      this.clear();
      if (window.showToast) window.showToast('تم إرسال طلبك بنجاح — أكمل التأكيد عبر واتساب');
    } catch (err) {
      console.error('Order submission failed:', err);
      if (!(window.navigator && window.navigator.onLine === false)) {
        this.setModalError('تعذر الاتصال بالخادم — تأكد من الإنترنت ثم أعد المحاولة');
      }
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalLabel;
      }
    }
  },

  // بالشراكات التالية بعد تحميل DOM
  bindEvents() {
    const itemsEl = document.getElementById('cartItems');
    if (itemsEl) itemsEl.addEventListener('click', (e) => {
      const btn = e.target.closest('.cart-item-remove');
      if (btn) this.remove(parseInt(btn.dataset.id));
    });

    const clearBtn = document.getElementById('clearCart');
    if (clearBtn) clearBtn.addEventListener('click', () => {
      if (confirm('مسح كل المنتجات من السلة؟')) {
        this.clear();
      }
    });

    const checkoutBtn = document.getElementById('checkoutBtn');
    if (checkoutBtn) checkoutBtn.addEventListener('click', () => this.openCheckout());

    const modal = this.getModal();
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) this.closeCheckout();
      });
      const cancelBtn = document.getElementById('checkoutCancel');
      if (cancelBtn) cancelBtn.addEventListener('click', () => this.closeCheckout());
    }

    const form = document.getElementById('checkout-form');
    if (form) form.addEventListener('submit', (e) => this.submitCheckout(e));
  }
};

// عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', () => {
  Cart.init();
  Cart.bindEvents();
  Cart.render();
});