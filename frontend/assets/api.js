/* api.js — helpers عامة: escaping إجباري لكل نص من قاعدة البيانات + fetch. */
"use strict";

function esc(v) {
  if (v === null || v === undefined) return "";
  return String(v)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

async function api(path, opts) {
  opts = opts || {};
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    ...opts,
  });
  let data = null;
  try { data = await resp.json(); } catch (_) { /* لا JSON */ }
  if (!resp.ok) {
    const detail = (data && data.detail) || `خطأ في الطلب (${resp.status})`;
    throw new Error(detail);
  }
  return data || {};
}

function money(n) {
  const num = Number(n) || 0;
  return num.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " شيكل";
}

function toast(msg, type) {
  const wrap = document.getElementById("toasts");
  if (!wrap) return;
  const el = document.createElement("div");
  el.className = "toast " + (type === "err" ? "err" : "ok");
  el.textContent = msg;
  wrap.appendChild(el);
  setTimeout(() => { el.remove(); }, 3500);
}