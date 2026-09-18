/* admin.js — لوحة التحكم: دخول، طلبات، منتجات، إعدادات. كل النصوص تُعرض عبر esc(). */
"use strict";

const $ = (id) => document.getElementById(id);

let ORDERS = [];
let PRODUCTS = [];

/* ── الجلسة ───────────────────────────── */
async function checkSession() {
  try {
    await api("/api/auth/me");
    return true;
  } catch (_) {
    return false;
  }
}

async function login(e) {
  e.preventDefault();
  const btn = $("loginBtn");
  btn.disabled = true;
  btn.textContent = "…";
  try {
    await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ password: $("adminPassword").value }),
    });
    enterShell();
  } catch (err) {
    toast(err.message, "err");
  } finally {
    btn.disabled = false;
    btn.textContent = "دخول";
  }
}

async function logout() {
  try { await api("/api/auth/logout", { method: "POST" }); } catch (_) {}
  location.reload();
}

function enterShell() {
  $("authScreen").style.display = "none";
  $("adminShell").classList.add("show");
  loadOverview();
  loadProductsTab();
  loadSettingsTab();
}

/* ── Tabs ─────────────────────────────── */
function switchTab(name) {
  document.querySelectorAll(".an-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.tab === name);
  });
  ["overview", "products", "settings"].forEach((t) => {
    $("tab-" + t).style.display = t === name ? "block" : "none";
  });
}

/* ── Overview: stats + orders ─────────── */
async function loadOverview() {
  try {
    const stats = await api("/api/orders/stats");
    const cards = [
      [stats.total_orders, "إجمالي الطلبات"],
      [stats.today_orders, "طلبات اليوم"],
      [stats.active_products, "منتجات متاحة"],
      [stats.total_revenue, "الإيرادات"],
    ];
    $("statCards").innerHTML = cards.map(([n, l]) =>
      '<div class="stat-card"><div class="num">' + esc(n) + "</div><div class=\"lbl\">" + esc(l) + "</div></div>"
    ).join("");
  } catch (err) {
    toast("فشل جلب الإحصائيات: " + err.message, "err");
  }
  await loadOrders();
}

async function loadOrders() {
  const filter = $("orderFilter").value;
  try {
    const res = await api("/api/orders" + (filter !== "all" ? "?status=" + encodeURIComponent(filter) : ""));
    ORDERS = res.orders || [];
  } catch (err) {
    toast(err.message, "err");
    ORDERS = [];
  }
  renderOrders();
}

const STATUS_CLASS = {
  pending: "status-pending", confirmed: "status-confirmed", preparing: "status-preparing",
  dispatched: "status-dispatched", delivered: "status-delivered", cancelled: "status-cancelled",
};

function renderOrders() {
  const tbody = $("ordersTable").querySelector("tbody");
  if (!ORDERS.length) {
    tbody.innerHTML = '<tr><td colspan="9" class="muted">لا توجد طلبات</td></tr>';
    return;
  }
  tbody.innerHTML = "";
  for (const o of ORDERS) {
    const tr = document.createElement("tr");
    const items = (o.items || []).map((i) =>
      esc(i.name) + " × " + esc(i.quantity) + ' <span class="muted">(' + esc(money(i.price)) + ")</span>"
    ).join("<br>") || "—";
    const statusSel =
      '<select data-order-status data-id="' + esc(o.id) + '">' +
      Object.entries(STATUS_CLASS).map(([val]) =>
        '<option value="' + val + '"' + (o.status === val ? " selected" : "") + ">" + val + "</option>"
      ).join("") +
      "</select>";
    tr.innerHTML =
      "<td>" + esc(o.id) + "</td>" +
      "<td>" + esc(o.customer_name || "—") + "</td>" +
      '<td dir="ltr">' + esc(o.customer_phone || "—") + "</td>" +
      "<td>" + items + "</td>" +
      "<td><b>" + esc(money(o.total)) + "</b></td>" +
      "<td>" + esc(o.branch_name || o.branch || "—") + "<br class=\"muted\">" + esc(o.delivery_zone || "") + "</td>" +
      '<td class="muted">' + esc(String(o.created_at || "").slice(0, 16)) + "</td>" +
      '<td><span class="status-tag ' + (STATUS_CLASS[o.status] || "status-pending") + '">' + esc(o.status) + "</span></td>" +
      "<td>" + statusSel + "</td>";
    tbody.appendChild(tr);
  }
}

async function changeOrderStatus(id, status) {
  try {
    await api("/api/orders/" + id + "/status", { method: "PUT", body: JSON.stringify({ status }) });
    toast("تم تحديث الحالة ✅", "ok");
    await loadOrders();
  } catch (err) {
    toast(err.message, "err");
  }
}

/* ── Products ─────────────────────────── */
async function loadProductsTab() {
  try {
    const res = await api("/api/products");
    PRODUCTS = res.products || [];
  } catch (err) {
    toast(err.message, "err");
    PRODUCTS = [];
  }
  renderProductsTable();
}

function renderProductsTable() {
  const tbody = $("productsTable").querySelector("tbody");
  if (!PRODUCTS.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="muted">لا توجد منتجات</td></tr>';
    return;
  }
  tbody.innerHTML = "";
  for (const p of PRODUCTS) {
    const tr = document.createElement("tr");
    tr.innerHTML =
      "<td>" + esc(p.id) + "</td>" +
      "<td>" + esc(p.name) + "</td>" +
      "<td>" + esc(p.category) + "</td>" +
      "<td>" + esc(money(p.price)) + "</td>" +
      '<td class="row">' +
        '<button class="btn btn-ghost btn-sm" data-edit="' + esc(p.id) + '" type="button">تعديل</button>' +
        '<button class="btn btn-danger btn-sm" data-del="' + esc(p.id) + '" type="button">حذف</button>' +
      "</td>";
    tbody.appendChild(tr);
  }
}

function fillProductForm(p) {
  $("pId").value = p ? p.id : "";
  $("pName").value = p ? p.name : "";
  $("pCategory").value = p ? p.category : "";
  $("pPrice").value = p ? p.price : "";
  $("pDesc").value = p ? p.desc : "";
  $("pIcon").value = p && p.icon ? p.icon : "medicine";
  $("pImage").value = p ? p.image : "";
  $("pSaveBtn").textContent = p ? "تحديث المنتج" : "إضافة المنتج";
}

async function saveProduct(e) {
  e.preventDefault();
  const id = $("pId").value;
  const body = {
    name: $("pName").value.trim(),
    category: $("pCategory").value.trim() || "أخرى",
    price: Number($("pPrice").value),
    desc: $("pDesc").value.trim(),
    icon: $("pIcon").value,
    image: $("pImage").value.trim(),
  };
  try {
    const url = id ? "/api/products/" + id : "/api/products";
    const method = id ? "PUT" : "POST";
    await api(url, { method, body: JSON.stringify(body) });
    toast("تم الحفظ ✅", "ok");
    fillProductForm(null);
    await loadProductsTab();
  } catch (err) {
    toast(err.message, "err");
  }
}

async function deleteProduct(id) {
  if (!confirm("حذف المنتج #" + id + " نهائيًا؟")) return;
  try {
    await api("/api/products/" + id, { method: "DELETE" });
    toast("تم الحذف", "ok");
    await loadProductsTab();
  } catch (err) {
    toast(err.message, "err");
  }
}

/* ── Settings ─────────────────────────── */
async function loadSettingsTab() {
  try {
    const res = await api("/api/settings");
    const s = res.settings || {};
    $("sName").value = s.name || "صيدلية السلاق";
    $("sAddress").value = s.address || "";
    $("sPhone").value = s.phone || "";
    $("sWaNumber").value = s.whatsapp_number || "9705952224444";
    $("sHours").value = s.hours || "";
    $("sWaToken").value = s.whatsapp_api_token || "";
    $("sWaPhoneId").value = s.whatsapp_phone_id || "";
    $("sWaBase").value = s.whatsapp_base_url || "";
  } catch (err) {
    toast(err.message, "err");
  }
}

async function saveSettings(e) {
  e.preventDefault();
  const body = {
    name: $("sName").value.trim(),
    address: $("sAddress").value.trim(),
    phone: $("sPhone").value.trim(),
    whatsapp_number: $("sWaNumber").value.trim(),
    hours: $("sHours").value.trim(),
    whatsapp_api_token: $("sWaToken").value.trim(),
    whatsapp_phone_id: $("sWaPhoneId").value.trim(),
    whatsapp_base_url: $("sWaBase").value.trim(),
  };
  try {
    const res = await api("/api/settings", { method: "PUT", body: JSON.stringify(body) });
    toast("تم حفظ الإعدادات ✅", "ok");
    loadSettingsFrom(res);
  } catch (err) {
    toast(err.message, "err");
  }
}

function loadSettingsFrom(res) {
  const s = res.settings || {};
  $("sWaToken").value = s.whatsapp_api_token || "";
}

/* ── init ─────────────────────────────── */
document.addEventListener("DOMContentLoaded", async () => {
  $("loginForm").addEventListener("submit", login);
  $("logoutBtn").addEventListener("click", logout);

  document.querySelectorAll(".an-btn[data-tab]").forEach((b) => {
    b.addEventListener("click", () => switchTab(b.dataset.tab));
  });

  $("orderFilter").addEventListener("change", loadOrders);
  $("ordersTable").addEventListener("change", (e) => {
    if (e.target.matches("[data-order-status]")) {
      changeOrderStatus(e.target.dataset.id, e.target.value);
    }
  });

  $("productForm").addEventListener("submit", saveProduct);
  $("pResetBtn").addEventListener("click", () => fillProductForm(null));
  $("productsTable").addEventListener("click", (e) => {
    const ed = e.target.closest("[data-edit]");
    const dl = e.target.closest("[data-del]");
    if (ed) {
      const p = PRODUCTS.find((x) => String(x.id) === String(ed.dataset.edit));
      if (p) fillProductForm(p);
    } else if (dl) {
      deleteProduct(dl.dataset.del);
    }
  });

  $("settingsForm").addEventListener("submit", saveSettings);

  if (await checkSession()) {
    enterShell();
  }
});