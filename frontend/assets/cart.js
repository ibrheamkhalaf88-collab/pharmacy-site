/* cart.js — حالة السلة محليًا (localStorage) + فتح/إغلاق + إرسال الطلب. */
"use strict";

const KEY = "salaq_cart_v2";
const CAR = {
  items: {}, // product_id -> { ...product, quantity }
  load() {
    try { this.items = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (_) { this.items = {}; }
    if (typeof this.items !== "object" || Array.isArray(this.items)) this.items = {};
    return this;
  },
  save() { localStorage.setItem(KEY, JSON.stringify(this.items)); },
  count() {
    return Object.values(this.items).reduce((s, it) => s + (Number(it.quantity) || 0), 0);
  },
  total() {
    return Object.values(this.items).reduce((s, it) => s + (Number(it.price) || 0) * (Number(it.quantity) || 0), 0);
  },
  add(product) {
    const id = String(product.id);
    if (this.items[id]) this.items[id].quantity += 1;
    else this.items[id] = { id: Number(id), name: product.name, price: Number(product.price), quantity: 1 };
    this.save();
  },
  remove(id) { delete this.items[String(id)]; this.save(); },
  setQty(id, q) {
    if (q <= 0) { this.remove(id); return; }
    this.items[String(id)].quantity = Math.min(q, 99);
    this.save();
  },
  asList() {
    return Object.values(this.items).map((i) => ({ product_id: i.id, quantity: i.quantity }));
  },
};

function openDrawer() {
  CAR.load();
  const d = document.getElementById("drawer");
  const o = document.getElementById("overlay");
  d.classList.add("open");
  o.classList.add("open");
  d.setAttribute("aria-hidden", "false");
  renderCart();
}

function closeDrawer() {
  const d = document.getElementById("drawer");
  const o = document.getElementById("overlay");
  d.classList.remove("open");
  o.classList.remove("open");
  d.setAttribute("aria-hidden", "true");
}

function renderCart() {
  const body = document.getElementById("cartBody");
  const badge = document.getElementById("cartBadge");
  const total = document.getElementById("cartTotal");
  const checkout = document.getElementById("checkoutBtn");

  const count = CAR.count();
  badge.textContent = count;
  badge.classList.toggle("active", count > 0);

  const items = Object.values(CAR.items);
  if (!items.length) {
    body.innerHTML = '<div class="cart-empty">السلة فارغة 🛒<br>أضف منتجات من المتجر</div>';
    total.textContent = "0.00 شيكل";
    checkout.disabled = true;
    return;
  }
  body.innerHTML = "";
  for (const it of items) {
    const el = document.createElement("div");
    el.className = "cart-item";
    el.innerHTML =
      '<div class="grow">' +
        '<div class="ci-name">' + esc(it.name) + "</div>" +
        '<div class="ci-price">' + esc(money(it.price)) + "</div>" +
      "</div>" +
      '<div class="qty">' +
        '<button type="button" data-act="dec" data-id="' + esc(it.id) + '">−</button>' +
        "<span>" + esc(it.quantity) + "</span>" +
        '<button type="button" data-act="inc" data-id="' + esc(it.id) + '">+</button>' +
      "</div>" +
      '<button class="remove-item" type="button" data-act="del" data-id="' + esc(it.id) + '" aria-label="حذف">🗑</button>';
    body.appendChild(el);
  }
  total.textContent = money(CAR.total());
  checkout.disabled = false;
}

async function submitOrder() {
  const name = document.getElementById("custName").value.trim();
  const phone = document.getElementById("custPhone").value.trim();
  const notes = document.getElementById("custNotes").value.trim();
  const btn = document.getElementById("checkoutBtn");

  if (!phone) {
    toast("أدخل رقم الهاتف حتى نتمكن من التواصل", "err");
    document.getElementById("custPhone").focus();
    return;
  }
  if (!CAR.asList().length) return;

  const digits = phone.replace(/\D/g, "");
  if (digits.length < 9 || digits.length > 15) {
    toast("رقم الهاتف غير صالح — تحقق منه", "err");
    return;
  }

  btn.classList.add("loading");
  btn.disabled = true;
  try {
    const res = await api("/api/orders", {
      method: "POST",
      body: JSON.stringify({
        customer_name: name,
        customer_phone: phone,
        notes: notes,
        items: CAR.asList(),
      }),
    });
    // نجح الطلب → احفظ واستعرض الواتساب
    CAR.items = {};
    CAR.save();
    closeDrawer();
    renderCart();
    toast("تم حفظ طلبك ✅ جاري فتح واتساب…", "ok");
    window.open(res.whatsapp_url, "_blank", "noopener");
  } catch (err) {
    toast(err.message, "err");
  } finally {
    btn.classList.remove("loading");
    btn.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  CAR.load();
  const drawer = document.getElementById("drawer");
  const overlay = document.getElementById("overlay");
  document.getElementById("openCart").addEventListener("click", openDrawer);
  document.getElementById("closeCart").addEventListener("click", closeDrawer);
  overlay.addEventListener("click", closeDrawer);
  document.getElementById("checkoutBtn").addEventListener("click", submitOrder);

  drawer.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-act]");
    if (!btn) return;
    const id = btn.dataset.id;
    const act = btn.dataset.act;
    if (act === "inc") CAR.setQty(id, (CAR.items[id]?.quantity || 0) + 1);
    else if (act === "dec") CAR.setQty(id, (CAR.items[id]?.quantity || 0) - 1);
    else if (act === "del") CAR.remove(id);
    renderCart();
  });

  // ESC يغلق السلة
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDrawer();
  });

  document.getElementById("cartBadge").textContent = CAR.count();
  document.getElementById("cartBadge").classList.toggle("active", CAR.count() > 0);
});