/**
 * صيدلية السلاق — JavaScript الرئيسي
 * يجلب المنتجات من الـ API ويعرضهم ببطاقات تحتوي صور(제품)
 * ويشغّل IntersectionObserver للأنيميشن + عداد المتحرك
 */
document.addEventListener('DOMContentLoaded', () => {

  // ═══════════════════════════════════════════════
  // 1. IntersectionObserver — Scroll animations
  // ═══════════════════════════════════════════════
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion:reduce)').matches;

  if (!prefersReducedMotion) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const delay = parseInt(el.dataset.delay || '0', 10);
          if (delay > 0) {
            el.style.transitionDelay = (delay * 0.08) + 's';
          }
          el.classList.add('reveal');
          observer.unobserve(el);
        }
      });
    }, {
      threshold: 0.12,
      rootMargin: '-40px 0px'
    });

    document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));
  } else {
    document.querySelectorAll('.animate-on-scroll').forEach(el => el.classList.add('reveal'));
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
    'دواء':    'img/medicine.jpg',
    'فيتامين': 'img/vitamins.jpg',
    'بشرة':    'img/skin.jpg',
    'أدوات':   'img/tools.jpg',
    'أخرى':    'img/medicine.jpg',
  };
  const defaultImage = 'img/medicine.jpg';

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
      const res = await fetch('/api/products');
      const data = await res.json();
      const products = data.products || [];

      productsGrid.innerHTML = products.map(p => {
        const cat = p.category || 'أخرى';
        const imgSrc = p.image || categoryImages[cat] || defaultImage;
        const imgAlt = cat === 'أدوات' ? 'أدوات طبية' : cat;
        return `
        <div class="product-card animate-on-scroll ${cat.replace(/\s/g,'')}" data-category="${cat}">
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

      // Observe freshly rendered cards so scroll animations apply to them too
      const freshCards = productsGrid.querySelectorAll('.product-card.animate-on-scroll:not(.reveal)');
      if (freshCards.length) {
        if (!prefersReducedMotion) {
          const cardObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
              if (entry.isIntersecting) {
                entry.target.classList.add('reveal');
                cardObserver.unobserve(entry.target);
              }
            });
          }, { threshold: 0.12, rootMargin: '-40px 0px' });
          freshCards.forEach(el => cardObserver.observe(el));
        } else {
          freshCards.forEach(el => el.classList.add('reveal'));
        }
      }
    } catch (err) {
      console.error('Error loading products:', err);
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
loadProducts();
if (typeof Cart !== 'undefined') Cart.render();
});
