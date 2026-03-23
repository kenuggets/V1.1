/* landing.js — Eyebrow → path draw-in (coil) → typewriter "Launchpad" */

(function () {
  const eyebrow     = document.querySelector('.hero-eyebrow');
  const paths       = document.querySelectorAll('#gemini-svg path');
  const labelLeft   = document.getElementById('label-left');
  const labelRight  = document.getElementById('label-right');
  const labelCenter = document.getElementById('label-center');
  const labelSub    = document.getElementById('label-center-sub');
  const heroText    = document.getElementById('hero-text');

  if (!paths.length) return;

  // Step 1 — eyebrow fades + slides up first
  const EYEBROW_DELAY    = 120;  // ms before eyebrow starts
  const EYEBROW_DURATION = 680;  // ms for eyebrow to finish
  const PATH_DELAY       = EYEBROW_DELAY + EYEBROW_DURATION - 100; // paths start near end of eyebrow

  setTimeout(() => {
    if (eyebrow) {
      eyebrow.style.opacity   = '1';
      eyebrow.style.transform = 'translateY(0)';
    }
  }, EYEBROW_DELAY);

  const lengths = Array.from(paths).map(p => {
    const len = p.getTotalLength();
    p.style.strokeDasharray  = len;
    p.style.strokeDashoffset = len;
    return len;
  });

  const TOTAL   = 3700;
  const STAGGER = 46;

  function easeIO(t) {
    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
  }

  // Custom draw curve: fast approach → very slow double-coil → fast exit
  // Coil zone is ~38–60% of path length (two oscillations), so we spend
  // 38% of total time drawing just 22% of the path there.
  function customDraw(t) {
    if (t <= 0) return 0;
    if (t >= 1) return 1;
    if (t < 0.36) {
      // approach: 36% time → 38% path
      return 0.38 * easeIO(t / 0.36);
    } else if (t < 0.76) {
      // coil: 40% time → 22% path  (very slow)
      return 0.38 + 0.22 * easeIO((t - 0.36) / 0.40);
    } else {
      // exit: 24% time → 40% path  (fast fan-out)
      return 0.60 + 0.40 * easeIO((t - 0.76) / 0.24);
    }
  }

  function startTypewriter() {
    const logoEl = document.querySelector('.gemini-center-logo');
    if (!logoEl) return;
    const text = logoEl.textContent.trim();
    logoEl.textContent = '';
    labelCenter.style.opacity = '1';
    text.split('').forEach((char, i) => {
      const span = document.createElement('span');
      span.textContent = char === ' ' ? '\u00a0' : char;
      span.style.cssText = 'opacity:0;display:inline-block;';
      logoEl.appendChild(span);
      setTimeout(() => {
        span.style.transition = 'opacity 0.14s ease';
        span.style.opacity = '1';
      }, i * 85);
    });
  }

  let startTime         = null;
  let typewriterStarted = false;
  let labelsStarted     = false;

  function tick(ts) {
    if (!startTime) startTime = ts;
    const elapsed = ts - startTime;
    const globalT = elapsed / TOTAL;

    paths.forEach((path, i) => {
      const delay = i * STAGGER;
      const t     = Math.max(0, Math.min(1, (elapsed - delay) / (TOTAL - delay)));
      path.style.strokeDashoffset = lengths[i] * (1 - customDraw(t));
    });

    // Side labels fade in just as coil starts (~38% mark)
    if (globalT > 0.36 && !labelsStarted) labelsStarted = true;
    if (labelsStarted) {
      const lT = Math.min(1, (globalT - 0.36) / 0.20);
      if (labelLeft)  labelLeft.style.opacity  = lT;
      if (labelRight) labelRight.style.opacity = lT;
    }

    // Typewriter at 80% (just after coil exits)
    if (globalT > 0.80 && !typewriterStarted) {
      typewriterStarted = true;
      startTypewriter();
    }

    // Subtitle at 90%
    if (labelSub)
      labelSub.style.opacity = Math.min(1, Math.max(0, (globalT - 0.90) / 0.08));

    // Hero text at 93%
    const tT = Math.min(1, Math.max(0, (globalT - 0.93) / 0.07));
    if (heroText) {
      heroText.style.opacity   = tT;
      heroText.style.transform = `translateY(${(1 - tT) * 28}px)`;
    }

    if (elapsed < TOTAL + STAGGER * paths.length + 800) requestAnimationFrame(tick);
  }

  setTimeout(() => requestAnimationFrame(tick), PATH_DELAY);
})();
