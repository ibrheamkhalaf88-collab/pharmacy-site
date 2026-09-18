/* app.js — تحميل المنتجات، الفئات، عرض البطاقات (escaping إجباري)، إضافة للسلة. */
"use strict";

const ICONS = {
  medicine: "/assets/img/medicine.svg",
  medical: "/assets/img/medical.svg",
  vitamin: "/assets/img/vitamin.svg",
  skin: "/assets/img/skin.svg",
  tools: "/assets/img/tools.svg",
  capsule: "/assets/img/capsule.svg",
};

let PRODUCTS = [];
let CURRENT = "all";

function iconSrc(name) {
  return ICONS[name] || ICONS.medical;
}

function fmtCategoryCount(cat) {
  return PRODUCTS.filter((p) => p.category === cat).length;
}

function renderCategories() {
  const box = document.getElementById("categories");
  const cats = ["all", ...new Set(PRODUCTS.map((p) => p.category))];
  box.innerHTML = "";
  for (const cat of cats) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "pill" + (cat === CURRENT ? " active" : "");
    b.textContent = cat === "all" ? "الكل" : cat + " (" + fmtCategoryCount(cat) + ")";
    b.dataset.cat = cat;
    b.addEventListener("click", () => {
      CURRENT = cat;
      renderCategories();
      renderProducts();
    });
    box.appendChild(b);
  }
}

function renderProducts() {
  const grid = document.getElementById("products");
  const list = CURRENT === "all" ? PRODUCTS : PRODUCTS.filter((p) => p.category === CURRENT);

  if (!list.length) {
    grid.innerHTML = '<div class="cart-empty" style="grid-column:1/-1">لا توجد منتجات حالياً</div>';
    return;
  }
  grid.innerHTML = "";
  for (const p of list) {
    const card = document.createElement("div");
    card.className = "card";
    card.appendChild(iconEl(p));
    const h3 = document.createElement("h3");
    h3.textContent = p.name;
    const desc = document.createElement("p");
    desc.textContent = p.desc || "";
    const bottom = document.createElement("div");
    bottom.className = "card-bottom";
    const pr = document.createElement("span");
    pr.className = "price";
    pr.textContent = money(p.price);
    const add = document.createElement("button");
    add.type = "button";
    add.className = "add-btn";
    add.textContent = "أضف للسلة";
    add.addEventListener("click", () => {
      CAR.add(p);
      renderCart();
      toast("تمت الإضافة ✅", "ok");
    });
    bottom.append(pr, add);
    card.append(h3, desc, bottom);
    grid.appendChild(card);
  }
}

function iconEl(p) {
  const wrap = document.createElement("div");
  wrap.className = "card-icon";
  const img = document.createElement("img");
  img.loading = "lazy";
  img.alt = p.name;
  if (p.image && /^https?:\/\//i.test(p.image)) {
    img.src = p.image;
    img.onerror = () => { img.src = iconSrc(p.icon); };
  } else {
    img.src = iconSrc(p.icon);
  }
  wrap.appendChild(img);
  return wrap;
}

async function loadProducts() {
  const grid = document.getElementById("products");
  grid.innerHTML = '<div class="cart-empty" style="grid-column:1/-1">⏳ جاري تحميل المنتجات…</div>';
  try {
    const res = await api("/api/products");
    PRODUCTS = res.products || [];
    renderCategories();
    renderProducts();
  } catch (err) {
    grid.innerHTML = '<div class="cart-empty" style="grid-column:1/-1">تعذر تحميل المنتجات: ' + esc(err.message) + "</div>";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadProducts();
});