/**
 * صيدلية سلاق — Premium Motion System v2.0
 * GSAP + ScrollTrigger + Lenis smooth scroll
 * ─────────────────────────────────────────
 * 1. Lenis smooth scroll synced with GSAP
 * 2. Hero entrance sequence (staggered on load)
 * 3. Word-by-word reveal with blur + y-offset
 * 4. Section fade-up reveals
 * 5. Flash cards curtain reveal
 * 6. Services cards stagger with rotation
 * 7. Contact pills slide
 * 8. Map cinematic entry
 * 9. Card hover tilt (mouse-reactive)
 * 10. Button micro-interactions
 * 11. Counter animation
 * 12. Scroll progress indicator
 * 13. Image parallax
 * 14. Sticky header shadow
 * ─────────────────────────────────────────
 */
(function () {
  'use strict';

  const wantsReduced =
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  // `?motion=on` يتجاوز تفضيلات النظام مؤقتاً (للمطور فقط) — يفعّل الأنميشن رغم إعدادات الجهاز
  const forceMotion =
    new URLSearchParams(window.location.search).has('motion') &&
    new URLSearchParams(window.location.search).get('motion') !== 'off';
  const reduced = wantsReduced && !forceMotion;
  const isCoarse = window.matchMedia('(pointer: coarse)').matches;
  const isMobile = window.innerWidth < 768 || isCoarse;

  if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;
  gsap.registerPlugin(ScrollTrigger);

  // ═══════════════════════════════════════════
  // 1. LENIS — Smooth Scroll synced with GSAP
  // ═══════════════════════════════════════════
  let lenis = null;
  if (!reduced && !isMobile && typeof Lenis !== 'undefined') {
    lenis = new Lenis({
      lerp: 0.08,
      smoothWheel: true,
      wheelMultiplier: 0.9,
      anchors: true,
    });
    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add((time) => { lenis.raf(time * 1000); });
    gsap.ticker.lagSmoothing(0);
  }

  // ═══════════════════════════════════════════
  // 14. SCROLL PROGRESS INDICATOR
  // ═══════════════════════════════════════════
  (function initScrollProgress() {
    if (reduced) return;
    const bar = document.createElement('div');
    bar.className = 'scroll-progress-bar';
    bar.setAttribute('aria-hidden', 'true');
    document.body.prepend(bar);

    gsap.to(bar, {
      scaleX: 1,
      ease: 'none',
      scrollTrigger: {
        trigger: document.body,
        start: 'top top',
        end: 'bottom bottom',
        scrub: 0.3,
      },
    });
  })();

  // ═══════════════════════════════════════════
  // 14b. STICKY HEADER SHADOW
  // ═══════════════════════════════════════════
  (function initStickyHeader() {
    const header = document.querySelector('header');
    if (!header) return;
    ScrollTrigger.create({
      start: 80,
      end: 99999,
      onToggle: (self) => {
        header.classList.toggle('header-scrolled', self.isActive);
      },
    });
  })();

  // ═══════════════════════════════════════════
  // 2. HERO — Entrance Sequence + Parallax
  // ═══════════════════════════════════════════
  (function initHero() {
    const hero = document.getElementById('hero-section');
    if (!hero) return;
    const mult = isMobile ? 0.45 : 1;

    // ── Entrance sequence (on page load) ──
    if (!reduced) {
      const heroTl = gsap.timeline({ delay: 0.2 });
      // Heading
      const h1 = hero.querySelector('h1, .font-headline-xl');
      if (h1) heroTl.from(h1, { y: 40, opacity: 0, duration: 0.8, ease: 'power3.out' });
      // Subtitle
      const sub = hero.querySelector('p.font-body-md, p.font-body-lg');
      if (sub) heroTl.from(sub, { y: 30, opacity: 0, duration: 0.7, ease: 'power3.out' }, '-=0.5');
      // CTA buttons
      const ctas = hero.querySelectorAll('a[href*="wa.me"], a[href*="consultation"], .pulse-gold');
      if (ctas.length) heroTl.from(ctas, { y: 20, opacity: 0, scale: 0.95, stagger: 0.1, duration: 0.6, ease: 'back.out(1.4)' }, '-=0.4');
      // Pharmacist image
      const imgWrap = hero.querySelector('[data-depth="3"]');
      if (imgWrap) heroTl.from(imgWrap, { x: isMobile ? 0 : 60, opacity: 0, scale: 0.92, duration: 0.9, ease: 'power3.out' }, '-=0.6');
      // Floating stat cards
      const stats = hero.querySelectorAll('[data-depth="5"]');
      if (stats.length) heroTl.from(stats, { y: 30, opacity: 0, scale: 0.8, stagger: 0.12, duration: 0.7, ease: 'back.out(1.6)' }, '-=0.5');
    }

    // ── Parallax (scroll-linked) ──
    // Background glows (depth 0)
    hero.querySelectorAll('[data-depth="0"]').forEach((el) => {
      gsap.to(el, {
        y: -70 * mult,
        x: 30 * mult,
        ease: 'none',
        scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: true },
      });
    });
    // Pharmacist image (depth 3) — scale up
    const imgWrap = hero.querySelector('[data-depth="3"]');
    if (imgWrap) {
      gsap.fromTo(imgWrap,
        { scale: 1 },
        { scale: 1.07 + 0.08 * mult, ease: 'none',
          scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: true } }
      );
    }
    // Floating cards (depth 5) — faster + gentle float
    hero.querySelectorAll('[data-depth="5"]').forEach((el, i) => {
      gsap.to(el, {
        y: -110 * mult,
        ease: 'none',
        scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: true },
      });
      if (!isMobile && !reduced) {
        gsap.to(el, {
          y: i % 2 ? -10 : 10,
          duration: 3.4 + i * 0.6,
          yoyo: true,
          repeat: -1,
          ease: 'sine.inOut',
        });
      }
    });
  })();

  // ═══════════════════════════════════════════
  // 3. WORD-BY-WORD REVEAL (with blur + y-offset)
  // ═══════════════════════════════════════════
  function splitToWords(el) {
    if (el.dataset.splitDone) return;
    const text = el.textContent;
    if (!text || !text.trim()) return;
    el.dataset.splitDone = '1';
    if (el.querySelector('svg, img, span[class*="svg"]')) return;
    const frag = document.createDocumentFragment();
    const words = text.split(/\s+/).filter(Boolean);
    words.forEach((w, i) => {
      const s = document.createElement('span');
      s.className = 'epic-word';
      s.textContent = w;
      frag.appendChild(s);
      if (i < words.length - 1) frag.appendChild(document.createTextNode('\u00A0'));
    });
    el.textContent = '';
    el.appendChild(frag);
  }

  if (!reduced) {
    const wordTargets = [
      '#flash-deals-section h2',
      '#products-section h2',
      '#services-section h2',
      '#hours-location-section h2',
      '#contact-section h2',
    ];
    wordTargets.forEach((sel) => {
      document.querySelectorAll(sel).forEach((h2) => {
        splitToWords(h2);
        const words = h2.querySelectorAll('.epic-word');
        if (!words.length) return;
        gsap.fromTo(
          words,
          { y: 40, autoAlpha: 0, filter: 'blur(6px)' },
          {
            y: 0,
            autoAlpha: 1,
            filter: 'blur(0px)',
            stagger: 0.055,
            ease: 'expo.out',
            duration: 0.7,
            scrollTrigger: {
              trigger: h2,
              start: 'top 85%',
              once: true,
            },
          }
        );
      });
    });
  }

  // ═══════════════════════════════════════════
  // 4. SECTION FADE-UP REVEALS (Now Slide-in from sides)
  // ═══════════════════════════════════════════
  if (!reduced) {
    // Reveal paragraph text, labels, and spans inside sections
    const revealSelectors = [
      '#flash-deals-section p',
      '#products-section p, #products-section span.text-primary',
      '#services-section p, #services-section span',
      '#hours-location-section p',
      '#contact-section p',
    ];
    let counter = 0;
    revealSelectors.forEach((sel) => {
      document.querySelectorAll(sel).forEach((el) => {
        // Skip if inside a word-split h2
        if (el.closest('.epic-word') || el.dataset.revealed) return;
        if (el.textContent.trim().length < 5) return;
        el.dataset.revealed = '1';
        
        const xOffset = (counter % 2 === 0) ? 60 : -60;
        counter++;

        gsap.fromTo(el,
          { x: xOffset, autoAlpha: 0, filter: 'blur(6px)' },
          {
            x: 0,
            autoAlpha: 1,
            filter: 'blur(0px)',
            duration: 0.8,
            ease: 'power3.out',
            scrollTrigger: {
              trigger: el,
              start: 'top 85%',
              once: true,
            },
          }
        );
      });
    });
  }

  // ═══════════════════════════════════════════
  // 5. FLASH DEALS — Curtain reveal + stagger
  // ═══════════════════════════════════════════
  if (!reduced) {
    const flashCards = gsap.utils.toArray('#flash-deals-section .grid > .group');
    if (flashCards.length) {
      flashCards.forEach((c) => { c.style.transition = 'none'; });
      gsap.fromTo(flashCards,
        { clipPath: 'inset(0 0 100% 0)', x: gsap.utils.wrap([60, -60]), autoAlpha: 0.4 },
        {
          clipPath: 'inset(0 0 0% 0)',
          x: 0,
          autoAlpha: 1,
          stagger: 0.14,
          duration: 1,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: '#flash-deals-section .grid',
            start: 'top 85%',
            once: true,
          },
          onComplete: () => {
            flashCards.forEach((c) => {
              c.style.transition = '';
              gsap.set(c, { clearProps: 'clipPath,opacity,transform' });
            });
          },
        }
      );
    }
  }

  // ═══════════════════════════════════════════
  // 6. SERVICES — Stagger with rotation
  // ═══════════════════════════════════════════
  if (!reduced) {
    const serviceCards = gsap.utils.toArray('#services-section .grid > .group');
    if (serviceCards.length) {
      serviceCards.forEach((c) => { c.style.transition = 'none'; });
      gsap.fromTo(serviceCards,
        { x: gsap.utils.wrap([80, -80]), autoAlpha: 0, scale: 0.9, rotate: gsap.utils.wrap([-1.5, 1.2, -0.8]) },
        {
          x: 0,
          autoAlpha: 1,
          scale: 1,
          rotate: 0,
          stagger: 0.12,
          duration: 0.9,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: '#services-section .grid',
            start: 'top 85%',
            once: true,
          },
          onComplete: () => {
            serviceCards.forEach((c) => {
              c.style.transition = '';
              gsap.set(c, { clearProps: 'opacity,transform' });
            });
          },
        }
      );
    }
  }

  // ═══════════════════════════════════════════
  // 7. CONTACT PILLS — Slide from right (RTL)
  // ═══════════════════════════════════════════
  if (!reduced) {
    const pills = gsap.utils.toArray('#contact-section .lg\\:col-span-5 .p-space-md');
    if (pills.length) {
      pills.forEach((p) => { p.style.transition = 'none'; });
      gsap.fromTo(pills,
        { x: 90, autoAlpha: 0 },
        {
          x: 0,
          autoAlpha: 1,
          stagger: 0.12,
          duration: 0.8,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: '#contact-section .lg\\:col-span-5',
            start: 'top 82%',
            once: true,
          },
          onComplete: () => {
            pills.forEach((p) => {
              p.style.transition = '';
              gsap.set(p, { clearProps: 'opacity,transform' });
            });
          },
        }
      );
    }
  }

  // ═══════════════════════════════════════════
  // 8. MAP — Cinematic clip reveal
  // ═══════════════════════════════════════════
  if (!reduced) {
    const mapCard = document.querySelector('#hours-location-section .rounded-2xl.overflow-hidden.shadow-lg');
    if (mapCard) {
      gsap.fromTo(mapCard,
        { clipPath: 'inset(8% 8% 8% 8%)', scale: 1.06 },
        {
          clipPath: 'inset(0% 0% 0% 0%)',
          scale: 1,
          duration: 1.1,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: mapCard,
            start: 'top 82%',
            once: true,
          },
          onComplete: () => gsap.set(mapCard, { clearProps: 'clipPath,transform' }),
        }
      );
    }
  }

  // ═══════════════════════════════════════════
  // 9. CARD HOVER TILT (mouse-reactive)
  // ═══════════════════════════════════════════
  if (!reduced && !isMobile) {
    const tiltCards = document.querySelectorAll('#flash-deals-section .group, #services-section .group');
    tiltCards.forEach((card) => {
      card.style.transition = 'none';
      const enter = () => {
        gsap.to(card, { scale: 1.02, duration: 0.35, ease: 'power2.out', overwrite: 'auto' });
      };
      const move = (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const cx = rect.width / 2;
        const cy = rect.height / 2;
        const rotateX = ((y - cy) / cy) * -4;
        const rotateY = ((x - cx) / cx) * 4;
        gsap.to(card, {
          rotateX, rotateY,
          transformPerspective: 800,
          duration: 0.4,
          ease: 'power2.out',
          overwrite: 'auto',
        });
      };
      const leave = () => {
        gsap.to(card, {
          rotateX: 0, rotateY: 0, scale: 1,
          duration: 0.5, ease: 'power3.out', overwrite: 'auto',
        });
      };
      card.addEventListener('mouseenter', enter);
      card.addEventListener('mousemove', move);
      card.addEventListener('mouseleave', leave);
    });
  }

  // ═══════════════════════════════════════════
  // 10. BUTTON MICRO-INTERACTIONS
  // ═══════════════════════════════════════════
  if (!reduced) {
    document.querySelectorAll('button, a.btn-in-cart, .product-card button').forEach((btn) => {
      btn.addEventListener('mousedown', () => {
        gsap.to(btn, { scale: 0.95, duration: 0.1, ease: 'power2.out' });
      });
      btn.addEventListener('mouseup', () => {
        gsap.to(btn, { scale: 1, duration: 0.3, ease: 'back.out(2)' });
      });
      btn.addEventListener('mouseleave', () => {
        gsap.to(btn, { scale: 1, duration: 0.3, ease: 'power2.out' });
      });
    });
  }

  // ═══════════════════════════════════════════
  // 11. COUNTER ANIMATION (numbers count up)
  // ═══════════════════════════════════════════
  if (!reduced) {
    const counters = document.querySelectorAll('[data-count]');
    counters.forEach((el) => {
      const target = parseInt(el.dataset.count, 10);
      if (isNaN(target)) return;
      const obj = { val: 0 };
      gsap.to(obj, {
        val: target,
        duration: 2,
        ease: 'power2.out',
        scrollTrigger: {
          trigger: el,
          start: 'top 85%',
          once: true,
        },
        onUpdate: () => {
          el.textContent = Math.round(obj.val).toLocaleString('ar-EG');
        },
      });
    });
  }

  // ═══════════════════════════════════════════
  // 13. IMAGE PARALLAX (subtle depth on images)
  // ═══════════════════════════════════════════
  if (!reduced) {
    document.querySelectorAll('.product-img, .product-card img').forEach((img) => {
      gsap.fromTo(img,
        { y: -12 },
        {
          y: 12,
          ease: 'none',
          scrollTrigger: {
            trigger: img,
            start: 'top bottom',
            end: 'bottom top',
            scrub: 1,
          },
        }
      );
    });
  }

  // ═══════════════════════════════════════════
  // REFRESH after images/fonts load
  // ═══════════════════════════════════════════
  window.addEventListener('load', () => {
    ScrollTrigger.refresh();
  });
})();
