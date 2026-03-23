/**
 * Glowing border effect — vanilla JS port of the React GlowingEffect component.
 * Tracks mouse position, rotates a white spotlight arc around .feature-card borders.
 */
(function () {
  'use strict';

  function shortestAngle(from, to) {
    return ((to - from + 180) % 360 + 360) % 360 - 180;
  }

  function initGlow() {
    const cards = document.querySelectorAll('.feature-card');
    if (!cards.length) return;

    const state = new Map();
    cards.forEach(card => {
      state.set(card, { current: 0, target: 0, raf: null, active: false });
    });

    function tick(card) {
      const s = state.get(card);
      if (!s || !s.active) return;
      const diff = shortestAngle(s.current, s.target);
      s.current += diff * 0.14;
      card.style.setProperty('--glow-start', s.current.toFixed(1));
      s.raf = Math.abs(diff) > 0.15
        ? requestAnimationFrame(() => tick(card))
        : null;
    }

    document.addEventListener('pointermove', (e) => {
      cards.forEach(card => {
        const r = card.getBoundingClientRect();
        const prox = 40;
        const near =
          e.clientX > r.left  - prox && e.clientX < r.right  + prox &&
          e.clientY > r.top   - prox && e.clientY < r.bottom + prox;

        const s = state.get(card);
        s.active = near;
        card.style.setProperty('--glow-active', near ? '1' : '0');

        if (near) {
          const cx = r.left + r.width  / 2;
          const cy = r.top  + r.height / 2;
          s.target = Math.atan2(e.clientY - cy, e.clientX - cx) * 180 / Math.PI + 90;
          if (!s.raf) s.raf = requestAnimationFrame(() => tick(card));
        }
      });
    }, { passive: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGlow);
  } else {
    initGlow();
  }
})();
