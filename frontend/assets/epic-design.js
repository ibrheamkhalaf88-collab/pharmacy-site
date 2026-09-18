/**
 * صيدلية السلاق — Epic Scroll Animations (GSAP + ScrollTrigger)
 * يضيف طبقات عمق (parallax) + إضاءة كلمات أثناء السكرول + كشف ستائري للبطاقات.
 * لا يلمس نظام الـ reveal القائم (IntersectionObserver) لبطاقات المنتجات.
 * يحترم prefers-reduced-motion ويخفّف التأثيرات على شاشات اللمس.
 */
(function () {
  'use strict';

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduced) return; // CSS الجاهز يظهر كل شيء مباشرة

  const isCoarse = window.matchMedia('(pointer: coarse)').matches;
  const isMobile = window.innerWidth < 768 || isCoarse;
  if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

  gsap.registerPlugin(ScrollTrigger);

  // ═══════════════════════════════════════════════════════════
  // 1. HERO — Parallax طبقي مع سكرول (درجات عمق data-depth)
  // ═══════════════════════════════════════════════════════════
  const hero = document.getElementById('hero-section');
  if (hero) {
    const mult = isMobile ? 0.45 : 1;

    // توهجات الخلفية (depth 0) — تتحرك ببطء بعكس الاتجاه
    hero.querySelectorAll('[data-depth="0"]').forEach((el) => {
      gsap.to(el, {
        y: -70 * mult,
        x: 30 * mult,
        ease: 'none',
        scrollTrigger: {
          trigger: hero,
          start: 'top top',
          end: 'bottom top',
          scrub: true,
        },
      });
    });

    // صورة الصيدلي (depth 3) — تكبير ناعم أثناء مغادرة الهيرو
    const imgWrap = hero.querySelector('[data-depth="3"]');
    if (imgWrap) {
      gsap.fromTo(
        imgWrap,
        { scale: 1 },
        {
          scale: 1.07 + 0.08 * mult,
          ease: 'none',
          scrollTrigger: {
            trigger: hero,
            start: 'top top',
            end: 'bottom top',
            scrub: true,
          },
        }
      );
    }

    // بطاقات الإحصاءات العائمة (depth 5) — سرعة أعلى + طفو دائم
    hero.querySelectorAll('[data-depth="5"]').forEach((el, i) => {
      gsap.to(el, {
        y: -110 * mult,
        ease: 'none',
        scrollTrigger: {
          trigger: hero,
          start: 'top top',
          end: 'bottom top',
          scrub: true,
        },
      });
      if (!isMobile) {
        gsap.to(el, {
          y: i % 2 ? -10 : 10,
          duration: 3.4 + i * 0.6,
          yoyo: true,
          repeat: -1,
          ease: 'sine.inOut',
        });
      }
    });
  }

  // ═══════════════════════════════════════════════════════════
  // 2. إضاءة الكلمات أثناء السكرول (Word-by-word lighting)
  //    للعناوين h2 النصية (غير الموجودة داخل nested العناصر الكبيرة)
  // ═══════════════════════════════════════════════════════════
  function splitToWords(el) {
    if (el.dataset.splitDone) return;
    const text = el.textContent;
    if (!text || !text.trim()) return;
    el.dataset.splitDone = '1';
    // لا نلمس العناصر التي تحتوي مكونات SVG/children
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
        { opacity: 0.16, y: 8, filter: 'blur(2px)' },
        {
          opacity: 1,
          y: 0,
          filter: 'blur(0px)',
          stagger: 0.05,
          ease: 'power1.out',
          scrollTrigger: {
            trigger: h2,
            start: 'top 78%',
            end: 'top 40%',
            scrub: isMobile ? 0.4 : true,
          },
        }
      );
    });
  });

  // ═══════════════════════════════════════════════════════════
  // 3. FLASH DEALS — كشف ستائري (curtain roll-up) + صعود متدرج
  // ═══════════════════════════════════════════════════════════
  const flashCards = gsap.utils.toArray('#flash-deals-section .grid > .group');
  if (flashCards.length) {
    flashCards.forEach((card) => {
      card.style.transition = 'none';
    });
    gsap.fromTo(
      flashCards,
      { clipPath: 'inset(0 0 100% 0)', y: 70, opacity: 0.4 },
      {
        clipPath: 'inset(0 0 0% 0)',
        y: 0,
        opacity: 1,
        stagger: 0.14,
        duration: 1,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: '#flash-deals-section .grid',
          start: 'top 85%',
        },
        onComplete: () => {
          flashCards.forEach((card) => {
            card.style.transition = '';
            gsap.set(card, { clearProps: 'clipPath,opacity,transform' });
          });
        },
      }
    );
  }

  // ═══════════════════════════════════════════════════════════
  // 4. SERVICES — صعود متتالٍ مع دوران خفيف (cinematic stagger)
  // ═══════════════════════════════════════════════════════════
  const serviceCards = gsap.utils.toArray('#services-section .grid > .group');
  if (serviceCards.length) {
    serviceCards.forEach((card) => {
      card.style.transition = 'none';
    });
    gsap.fromTo(
      serviceCards,
      { y: 80, opacity: 0, scale: 0.9, rotate: gsap.utils.wrap([-1.5, 1.2, -0.8]) },
      {
        y: 0,
        opacity: 1,
        scale: 1,
        rotate: 0,
        stagger: 0.12,
        duration: 0.9,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: '#services-section .grid',
          start: 'top 85%',
        },
        onComplete: () => {
          serviceCards.forEach((card) => {
            card.style.transition = '';
            gsap.set(card, { clearProps: 'opacity,transform' });
          });
        },
      }
    );
  }

  // ═══════════════════════════════════════════════════════════
  // 5. CONTACT PILLS — انزلاق متتالٍ من اليمين في (RTL)
  // ═══════════════════════════════════════════════════════════
  const pills = gsap.utils.toArray('#contact-section .lg\\:col-span-5 .p-space-md');
  if (pills.length) {
    pills.forEach((p) => { p.style.transition = 'none'; });
    gsap.fromTo(
      pills,
      { x: 90, opacity: 0 },
      {
        x: 0,
        opacity: 1,
        stagger: 0.12,
        duration: 0.8,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: '#contact-section .lg\\:col-span-5',
          start: 'top 82%',
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

  // ═══════════════════════════════════════════════════════════
  // 6. MAP — دخول سينمائي (Zoom via clip) + توهج بطاقة تشخيصية
  // ═══════════════════════════════════════════════════════════
  const mapCard = document.querySelector('#hours-location-section .rounded-2xl.overflow-hidden.shadow-lg');
  if (mapCard) {
    gsap.fromTo(
      mapCard,
      { clipPath: 'inset(8% 8% 8% 8%)', scale: 1.06 },
      {
        clipPath: 'inset(0% 0% 0% 0%)',
        scale: 1,
        duration: 1.1,
        ease: 'power2.out',
        scrollTrigger: {
          trigger: mapCard,
          start: 'top 82%',
        },
        onComplete: () => gsap.set(mapCard, { clearProps: 'clipPath,transform' }),
      }
    );
  }

  // refresh بعد تحميل الصور والخطوط لضبط المقاسات
  window.addEventListener('load', () => ScrollTrigger.refresh());
})();