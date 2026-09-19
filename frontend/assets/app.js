/**
 * صيدلية السلاق — JavaScript الرئيسي
 * يجلب المنتجات من الـ API ويعرضهم ببطاقات تحتوي صور(제품)
 * ويشغّل IntersectionObserver للأنيميشن + عداد المتحرك
 */
document.addEventListener('DOMContentLoaded', () => {

  // ═══════════════════════════════════════════════
  // 1. IntersectionObserver — Scroll animations (تحسين: stagger مدروس لكل عنصر)
  // ═══════════════════════════════════════════════
  const wantsReducedMotion = window.matchMedia('(prefers-reduced-motion:reduce)').matches;
  // `?motion=on` يتجاوز تفضيلات النظام (للمطور) — نفس log'ic المتبعة في epic-design.js
  const forceMotion =
    new URLSearchParams(window.location.search).has('motion') &&
    new URLSearchParams(window.location.search).get('motion') !== 'off';
  const prefersReducedMotion = wantsReducedMotion && !forceMotion;

  //Stagger delays by category of element for "just-appeared" feel
  const staggerMap = {
    '.product-card':     0.08,   // 80ms بين كل منتج — تشوّيش خفيف يشبه " emergence"
    '.service-card':     0.07,
    '.category-card':    0.06,
    '.testimonial-card': 0.09,
    '.counter-item':     0.05,
    '.about-features li':0.06,
    '.slide-left':       0.10,
    '.slide-right':      0.10,
    '.scale-in':         0.08,
    '.fade-up':          0.06,
    '.page-load-anim':   0.08,   // handled separately in page-load stagger
    '.stagger-children > *': 0.05,
  };

  function getStaggerDelay(el) {
    for (const selector in staggerMap) {
      if (el.matches(selector) || el.closest(selector)) {
        const base = staggerMap[selector];
        // index-based increment for siblings
        const parent = el.closest(':scope > *') || el.parentElement;
        if (parent) {
          const siblings = [...parent.children].filter(c => c.matches && c.matches(selector));
          const idx = siblings.indexOf(el);
          if (idx >= 0) return base + idx * base * 0.6; // exponential-ish spread
        }
        return base;
      }
    }
    return 0.06; // default
  }

  if (!prefersReducedMotion) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          // Skip if already revealed
          if (el.classList.contains('reveal')) return;
          // Apply stagger delay
          const delay = getStaggerDelay(el);
          el.style.transitionDelay = delay + 's';
          // Add the reveal class (CSS handles the actual animation)
          el.classList.add('reveal');
          // Unobserve after reveal (performance)
          observer.unobserve(el);
        }
      });
    }, {
      threshold: 0.10,
      rootMargin: '-30px 0px -20px 0px'   // trigger slightly before center
    });

    document.querySelectorAll('.animate-on-scroll, .slide-left, .slide-right, .scale-in, .fade-up').forEach(el => observer.observe(el));
  } else {
    document.querySelectorAll('.animate-on-scroll, .slide-left, .slide-right, .scale-in, .fade-up').forEach(el => el.classList.add('reveal'));
  }

  // ═══════════════════════════════════════════════
  // 2. Counter Animation (Number ticker)
  // ═══════════════════════════════════════════════
  function animateCounter(el, target, duration = 1400) {
    const start = performance.now();
    const isFloat = target % 1 !== 0;

    function tick(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out quad
      const eased = 1 - (1 - progress) * (1 - progress);
      const current = eased * target;
      el.textContent = isFloat
        ? current.toFixed(1).replace(/\.0$/, '')
        : Math.floor(current).toLocaleString('ar-EG');
      if (progress < 1) {
        requestAnimationFrame(tick);
      } else {
        el.textContent = isFloat
          ? target.toFixed(1).replace(/\.0$/, '')
          : target.toLocaleString('ar-EG');
      }
    }
    requestAnimationFrame(tick);
  }

  // ═══════════════════════════════════════════════
  // 3. Init counters when they scroll into view
  // ═══════════════════════════════════════════════
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const section = entry.target;
        section.querySelectorAll('[data-target]').forEach(el => {
          const target = parseInt(el.dataset.target, 10);
          if (!isNaN(target) && target > 0) {
            animateCounter(el, target);
          }
        });
        counterObserver.unobserve(section);
      }
    });
  }, { threshold: 0.4 });

  const countersSection = document.getElementById('stats');
  if (countersSection) counterObserver.observe(countersSection);

  // Also check if counters are already visible at load
  if (countersSection && countersSection.getBoundingClientRect().top < window.innerHeight) {
    countersSection.querySelectorAll('[data-target]').forEach(el => {
      const target = parseInt(el.dataset.target, 10);
      if (!isNaN(target) && target > 0) {
        animateCounter(el, target);
      }
    });
  }

  // ═══════════════════════════════════════════════
  // 4. Floating WhatsApp button — scroll tracking + click
  // ═══════════════════════════════════════════════
  const floatingWA = document.createElement('a');
  floatingWA.className = 'floating-wa';
  floatingWA.href = 'https://wa.me/9705952224444?text=مرحباً%2C%20بدي%20أطلب%20من%20صيدلية%20السلاق';
  floatingWA.target = '_blank';
  floatingWA.rel = 'noopener';
  floatingWA.setAttribute('aria-label', 'اتصل بنا على واتساب');
  floatingWA.innerHTML = `
    <span class="pulse-ring"></span>
    <span class="wa-tooltip">اتصل الآن</span>
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.148-.198.297-.768.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.724-1.7-2.056-1.99-.333-.29-.528-.328-.79-.15-.265.18-.55.63-.556 1.008-.005.378.198.703.526.928.328.225.656.27.855.303.199.034.428.052.672.052.405 0 .766-.043 1.084-.274.32-.23.498-.513.622-.85.123-.338.25-.73.373-1.113.123-.385.303-.64.527-.824.225-.184.48-.26.734-.25.255.01.462.104.612.28.15.174.225.427.225.708 0 .28-.074.515-.148.684-.297.654-.783 1.46-1.168 1.93-.385.47-.776.69-.977.917-.201.227-.27.293-.458.249-.188-.044-.326-.18-.5-.416-.333-.47-.438-1.024-.374-1.435.065-.412.224-.753.43-1.042.206-.288.468-.54.734-.463.267.076.468.324.707.495.24.17.497.265.714.37.216.105.443.024.573-.147.13-.17.205-.402.22-.612.018-.247-.073-.478-.22-.65-.147-.172-.37-.26-.602-.26z"/>
      <path d="M12 0c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm0 22c-5.523 0-10-4.477-10-10s4.477-10 10-10 10 4.477 10 10-4.477 10-10 10z"/>
    </svg>
  `;
  document.body.appendChild(floatingWA);

  // ═══════════════════════════════════════════════
  // 5. Category cards — filter on click
  // ═══════════════════════════════════════════════
  document.querySelectorAll('.category-card').forEach(card => {
    card.addEventListener('click', () => {
      const filter = card.dataset.filter || 'all';
      applyFilter(filter);
      document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.cat === filter);
      });
    });
  });

  // ═══════════════════════════════════════════════
  // 6. Products loading + filters
  // ═══════════════════════════════════════════════
  const productsGrid = document.getElementById('productsGrid') || document.getElementById('products-grid');

  const categoryImages = {
    'دواء':    '/assets/img/medicine.svg',
    'فيتامين': '/assets/img/vitamins.svg',
    'بشرة':    '/assets/img/skin.svg',
    'أدوات':   '/assets/img/tools.svg',
    'أخرى':    '/assets/img/medicine.svg',
  };
  const defaultImage = '/assets/img/medicine.svg';

  // ── filterProducts (called from index.html tabs) ──
  window.filterProducts = function(category, btnEl) {
    if (btnEl) {
      document.querySelectorAll('.product-tab-btn').forEach(b => {
        b.classList.remove('bg-primary','text-on-primary','font-bold');
        b.classList.add('text-on-surface-variant');
      });
      btnEl.classList.add('bg-primary','text-on-primary','font-bold');
      btnEl.classList.remove('text-on-surface-variant');
    }
    const cards = document.querySelectorAll('.product-card');
    cards.forEach(c => {
      const match = category === 'all' || c.dataset.category === category;
      c.style.display = match ? '' : 'none';
      c.style.opacity = match ? '1' : '.4';
    });
  };

  async function loadProducts() {
    if (!productsGrid) return;
    try {
      // Show skeleton placeholders while loading
      productsGrid.innerHTML = Array.from({ length: 6 }, () => `
        <div class="product-card skeleton-load">
          <div style="width:100%;height:160px;background:var(--gray-200);border-radius:0"></div>
          <div class="product-body" style="padding:16px">
            <div class="skeleton" style="width:70%;height:18px"></div>
            <div class="skeleton" style="width:100%;height:14px;margin-top:8px"></div>
            <div class="skeleton" style="width:50%;height:22px;margin-top:12px"></div>
          </div>
        </div>
      `).join('');

      const res = await fetch('/api/products');
      const data = await res.json();
      const products = data.products || [];

      productsGrid.innerHTML = products.map((p, idx) => {
        const cat = p.category || 'أخرى';
        const imgSrc = p.image || categoryImages[cat] || defaultImage;
        const imgAlt = cat === 'أدوات' ? 'أدوات طبية' : cat;
        // Stagger delay: each card gets idx * 0.08s (80ms apart)
        const stagger = (idx % 12) * 0.08;
        return `
        <div class="product-card ${cat.replace(/\s/g,'')}" data-category="${cat}" style="opacity:0; transform:translateY(40px) scale(0.96) ${idx % 2 ? 'translateX(-6px)' : 'translateX(6px)'}; transition-delay:${stagger}s">
          <img src="${imgSrc}" alt="${imgAlt}" class="product-img" loading="lazy" onerror="this.src='${defaultImage}'">
          <div class="product-body">
            <h3 class="product-name">${p.name}</h3>
            <p class="product-desc">${p.desc}</p>
            <div class="product-price">${p.price.toFixed(2)} <span>شيكل</span></div>
            <button class="btn-in-cart" onclick="addToCart(${JSON.stringify(p).replace(/"/g,'&quot;')})">
              أضف للطلب
            </button>
          </div>
        </div>`;
      }).join('');

      // Reveal all cards with staggered timing — each appears little by little
      const allCards = productsGrid.querySelectorAll('.product-card:not(.skeleton-load)');
      if (allCards.length && !prefersReducedMotion) {
        // Wait briefly so the browser paints the initial state, then stagger-reveal
        setTimeout(() => {
          allCards.forEach((card, i) => {
            setTimeout(() => {
              card.style.opacity = '';
              card.style.transform = '';
              card.classList.add('reveal');
            }, i * 80); // 80ms between each card = "just appeared" feel
          });
        }, 200);
      } else if (allCards.length) {
        // Reduced-motion: reveal instantly — MUST clear the inline hidden state too,
        // otherwise cards stay invisible (inline opacity overrides CSS)
        allCards.forEach(c => {
          c.style.opacity = '';
          c.style.transform = '';
          c.classList.add('reveal');
        });
      }
    } catch (err) {
      console.error('Error loading products:', err);
      if (productsGrid) {
        productsGrid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--gray-400)">عذراً، لم يتم تحميل المنتجات. حاول تحديث الصفحة.</div>';
      }
    }
  }

  // Keep inline (static cards) addToCart(this, name) working alongside
  // dynamic addToCart(productObj) — dispatch by argument type.
  const legacyAddToCart = (typeof window.addToCart === 'function') ? window.addToCart : null;
  window.addToCart = function(productOrBtn, productName) {
    if (productOrBtn && productOrBtn.tagName) {
      if (legacyAddToCart) return legacyAddToCart(productOrBtn, productName);
      if (window.showToast) window.showToast('تمت الإضافة: ' + (productName || ''));
      return;
    }
    const product = productOrBtn;
    if (typeof Cart !== 'undefined' && product && product.id) {
      Cart.add(product);
    }
    const btn = (typeof event !== 'undefined' && event && event.target) ? event.target.closest('.btn-in-cart') : null;
    if (btn) {
      btn.textContent = '✓ في السلة';
      btn.disabled = true;
      setTimeout(() => {
        btn.textContent = 'أضف للطلب';
        btn.disabled = false;
      }, 1500);
    }
  };

  function applyFilter(category) {
    document.querySelectorAll('.filter-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.cat === category);
    });
    document.querySelectorAll('.category-card').forEach(card => {
      card.style.opacity = (category === 'all' || card.dataset.filter === category) ? '1' : '.4';
    });

    const cards = document.querySelectorAll('.product-card');
    if (category === 'all') {
      cards.forEach(c => c.style.display = '');
    } else {
      cards.forEach(c => {
        c.style.display = c.dataset.category === category ? '' : 'none';
      });
    }
  }

  document.querySelectorAll('.filter-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      applyFilter(tab.dataset.cat);
    });
  });

  // ═══════════════════════════════════════════════
  // 7. Offers ticker pause on hover
  // ═══════════════════════════════════════════════
  const offersTrack = document.getElementById('offersTrack');
  if (offersTrack) {
    offersTrack.addEventListener('mouseenter', () => {
      offersTrack.style.animationPlayState = 'paused';
    });
    offersTrack.addEventListener('mouseleave', () => {
      offersTrack.style.animationPlayState = 'running';
    });
  }

// ═══════════════════════════════════════════════
// 8. Scroll Progress Bar
// ═══════════════════════════════════════════════
const scrollProgress = document.createElement('div');
scrollProgress.className = 'scroll-progress';
document.body.appendChild(scrollProgress);
// Fallback for browsers without scroll-driven animations support
if (!window.CSS || !CSS.supports || !CSS.supports('animation-timeline: scroll()')) {
  scrollProgress.style.display = 'block';
  const updateProgress = () => {
    const h = document.documentElement;
    const max = h.scrollHeight - h.clientHeight;
    const p = max > 0 ? h.scrollTop / max : 0;
    scrollProgress.style.transform = 'scaleX(' + p + ')';
  };
  window.addEventListener('scroll', updateProgress, { passive: true });
  updateProgress();
}

// ═══════════════════════════════════════════════
// 9. Page Load Stagger Animation
// ═══════════════════════════════════════════════
document.querySelectorAll('.page-load-anim').forEach((el, i) => {
  el.style.transitionDelay = `${i * 0.1}s`;
  setTimeout(() => el.classList.add('anim-in'), 80 + i * 100);
});

// ═══════════════════════════════════════════════
// 10. Stagger Children Animation
// ═══════════════════════════════════════════════
document.querySelectorAll('.stagger-children').forEach(container => {
  if (!prefersReducedMotion) {
    const children = container.querySelectorAll(':scope > *');
    children.forEach((child, i) => {
      child.style.transitionDelay = `${i * 0.08}s`;
    });
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          container.classList.add('reveal');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    observer.observe(container);
  } else {
    container.classList.add('reveal');
  }
});

// ═══════════════════════════════════════════════
// 11. Toast Notification System
// ═══════════════════════════════════════════════
window.showToast = function(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.style.cssText = `
    position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%) translateX(2rem);
    background: var(--green-900); color: #fff; padding: 12px 24px;
    border-radius: 10px; font-size: 14px; font-weight: 600; z-index: 9999;
    box-shadow: var(--shadow-lg); transition: opacity .3s, transform .3s;
    opacity: 0; font-family: 'Tajawal', system-ui, sans-serif;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);
  requestAnimationFrame(() => { toast.style.opacity = '1'; toast.style.transform = 'translateX(-50%) translateX(0)'; });
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(-50%) translateX(-2rem)'; setTimeout(() => toast.remove(), 300); }, 3000);
};

// ═══════════════════════════════════════════════
// 12. Cart Bar Animation
// ═══════════════════════════════════════════════
const cartBar = document.querySelector('.cart-bar');
if (cartBar && typeof Cart !== 'undefined') {
  const origRender = Cart.render.bind(Cart);
  Cart.render = function() {
    origRender();
    const hasItems = document.querySelectorAll('.cart-item').length > 0;
    cartBar.classList.toggle('visible', hasItems);
  };
}

// ═══════════════════════════════════════════════
// 8. Init
// ═══════════════════════════════════════════════
// ── سحب شريط أقسام المنتجات يمين/يسار (drag-to-scroll) ──
(function initProductsStrip() {
  const strip = document.getElementById('product-tabs');
  if (!strip) return;
  let isDown = false, startX = 0, startScroll = 0, moved = false;
  strip.addEventListener('pointerdown', (e) => {
    isDown = true; moved = false;
    startX = e.clientX;
    startScroll = strip.scrollLeft;
    strip.setPointerCapture && strip.setPointerCapture(e.pointerId);
  });
  strip.addEventListener('pointermove', (e) => {
    if (!isDown) return;
    const dx = e.clientX - startX;
    if (Math.abs(dx) > 5) moved = true;
    // في الصفحات العربية (RTL) تمرير scrollLeft سالب — نعكس الإشارة.
    const rtl = getComputedStyle(strip).direction === 'rtl';
    strip.scrollLeft = startScroll + (rtl ? dx : -dx);
  });
  const stop = (e) => {
    if (moved && e && e.preventDefault) e.preventDefault();
    isDown = false;
  };
  strip.addEventListener('pointerup', stop);
  strip.addEventListener('pointercancel', () => { isDown = false; });
})();

loadProducts();
if (typeof Cart !== 'undefined') Cart.render();
});
