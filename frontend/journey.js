/* journey.js — Three.js scroll-driven 3-stage journey (Discover → Build → Prepare) */

(function () {
  const section = document.getElementById('journey-section');
  const canvas  = document.getElementById('journey-canvas');
  if (!section || !canvas || typeof THREE === 'undefined') return;

  const COUNT = 1400;

  // ─── SCENE SETUP ────────────────────────────────────────────────────────────
  const scene    = new THREE.Scene();
  scene.fog      = new THREE.FogExp2(0x000000, 0.005);

  const camera   = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.set(0, 4, 80);
  camera.lookAt(0, 0, 0);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // ─── STAR FIELD ─────────────────────────────────────────────────────────────
  const starGeo = new THREE.BufferGeometry();
  const starPos = new Float32Array(3000 * 3);
  for (let i = 0; i < 3000; i++) {
    const r = 300 + Math.random() * 500;
    const theta = Math.random() * Math.PI * 2;
    const phi   = Math.acos(2 * Math.random() - 1);
    starPos[i*3]   = r * Math.sin(phi) * Math.cos(theta);
    starPos[i*3+1] = r * Math.sin(phi) * Math.sin(theta);
    starPos[i*3+2] = r * Math.cos(phi);
  }
  starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
  const starMat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.35, transparent: true, opacity: 0.5, depthWrite: false });
  const stars = new THREE.Points(starGeo, starMat);
  scene.add(stars);

  // ─── MAIN PARTICLE SYSTEM ───────────────────────────────────────────────────
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(COUNT * 3);
  const col = new Float32Array(COUNT * 3);
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('color',    new THREE.BufferAttribute(col, 3));

  const mat = new THREE.PointsMaterial({
    size: 0.7,
    vertexColors: true,
    transparent: true,
    opacity: 0.88,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const particles = new THREE.Points(geo, mat);
  scene.add(particles);

  // ─── 3 FORMATIONS ───────────────────────────────────────────────────────────
  // F0 — scattered sphere (Discover / University)
  // F1 — double helix stream (Build / Intern momentum)
  // F2 — structured grid plane (Prepare / Professional)

  const f0 = new Float32Array(COUNT * 3);
  const f1 = new Float32Array(COUNT * 3);
  const f2 = new Float32Array(COUNT * 3);
  const c0 = new Float32Array(COUNT * 3); // amber
  const c1 = new Float32Array(COUNT * 3); // sky-blue
  const c2 = new Float32Array(COUNT * 3); // clean white-blue

  const gridW = Math.ceil(Math.sqrt(COUNT));

  for (let i = 0; i < COUNT; i++) {
    // ── Formation 0: scattered sphere
    const r0  = 28 + Math.random() * 22;
    const th0 = Math.random() * Math.PI * 2;
    const ph0 = Math.acos(2 * Math.random() - 1);
    f0[i*3]   = r0 * Math.sin(ph0) * Math.cos(th0);
    f0[i*3+1] = r0 * Math.sin(ph0) * Math.sin(th0);
    f0[i*3+2] = r0 * Math.cos(ph0);
    c0[i*3]   = 0.97; c0[i*3+1] = 0.63; c0[i*3+2] = 0.05; // amber

    // ── Formation 1: double-helix upward stream
    const t1     = i / COUNT;
    const angle1 = t1 * Math.PI * 14;
    const sign1  = i % 2 === 0 ? 1 : -1;
    const rad1   = 9 + Math.random() * 3;
    f1[i*3]   = Math.cos(angle1) * rad1 * sign1 + (Math.random() - 0.5) * 5;
    f1[i*3+1] = t1 * 90 - 45;
    f1[i*3+2] = Math.sin(angle1) * rad1 + (Math.random() - 0.5) * 3;
    c1[i*3]   = 0.36; c1[i*3+1] = 0.65; c1[i*3+2] = 0.98; // sky blue

    // ── Formation 2: flat grid
    const gx = (i % gridW) - gridW / 2;
    const gy = Math.floor(i / gridW) - gridW / 2;
    f2[i*3]   = gx * 4.2;
    f2[i*3+1] = gy * 4.2;
    f2[i*3+2] = (Math.sin(gx * 0.35) + Math.cos(gy * 0.35)) * 3.5;
    c2[i*3]   = 0.88; c2[i*3+1] = 0.95; c2[i*3+2] = 1.0; // cool white
  }

  // Seed positions at formation 0
  for (let i = 0; i < COUNT * 3; i++) { pos[i] = f0[i]; col[i] = c0[i]; }
  geo.attributes.position.needsUpdate = true;
  geo.attributes.color.needsUpdate    = true;

  // ─── CAMERA TARGETS PER STAGE ───────────────────────────────────────────────
  const camTargets = [
    { x: 0, y:  4, z: 80 },  // Discover
    { x: 0, y: 14, z: 65 },  // Build
    { x: 0, y: 24, z: 50 },  // Prepare
  ];
  const smoothCam = { x: 0, y: 4, z: 80 };
  let   targetCam = { x: 0, y: 4, z: 80 };

  // ─── SCROLL STATE ───────────────────────────────────────────────────────────
  let scrollT = 0; // 0 → 2 continuous

  function lerp(a, b, t) { return a + (b - a) * t; }

  function onScroll() {
    const rect    = section.getBoundingClientRect();
    const scrolled = -rect.top;
    const total   = section.offsetHeight - window.innerHeight;
    const progress = Math.max(0, Math.min(1, scrolled / total));
    scrollT = progress * 2;

    // Stage indicator dots
    const stage = Math.min(2, Math.floor(scrollT));
    document.querySelectorAll('.jp-dot').forEach((d, i) => {
      d.classList.toggle('active', i === stage);
    });

    // Text panels — fade & slide based on proximity to integer stage
    document.querySelectorAll('.journey-stage').forEach((el, i) => {
      const dist = Math.abs(scrollT - i);
      el.style.opacity   = Math.max(0, 1 - dist * 2.2).toFixed(3);
      el.style.transform = `translateY(${(scrollT - i) * 44}px)`;
    });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ─── RENDER LOOP ────────────────────────────────────────────────────────────
  function animate() {
    requestAnimationFrame(animate);
    const time = Date.now() * 0.001;

    // Rotate star field slowly
    stars.rotation.y = time * 0.018;
    stars.rotation.x = time * 0.006;

    // Lerp particles between formations
    const t     = Math.min(1.999, scrollT);
    const stage = Math.floor(t);
    const frac  = t - stage;

    const fromP = stage === 0 ? f0 : f1;
    const toP   = stage === 0 ? f1 : f2;
    const fromC = stage === 0 ? c0 : c1;
    const toC   = stage === 0 ? c1 : c2;

    for (let i = 0; i < COUNT; i++) {
      const ii = i * 3;
      pos[ii]   = lerp(fromP[ii],   toP[ii],   frac) + Math.sin(time * 0.6 + i * 0.09) * 0.06;
      pos[ii+1] = lerp(fromP[ii+1], toP[ii+1], frac) + Math.cos(time * 0.5 + i * 0.11) * 0.06;
      pos[ii+2] = lerp(fromP[ii+2], toP[ii+2], frac);
      col[ii]   = lerp(fromC[ii],   toC[ii],   frac);
      col[ii+1] = lerp(fromC[ii+1], toC[ii+1], frac);
      col[ii+2] = lerp(fromC[ii+2], toC[ii+2], frac);
    }
    geo.attributes.position.needsUpdate = true;
    geo.attributes.color.needsUpdate    = true;

    // Smooth camera
    const cs   = Math.min(2, Math.floor(scrollT));
    const cf   = Math.min(1, scrollT - cs);
    const cFrom = camTargets[cs];
    const cTo   = camTargets[Math.min(2, cs + 1)];
    targetCam.x = lerp(cFrom.x, cTo.x, cf);
    targetCam.y = lerp(cFrom.y, cTo.y, cf);
    targetCam.z = lerp(cFrom.z, cTo.z, cf);

    smoothCam.x = lerp(smoothCam.x, targetCam.x, 0.045);
    smoothCam.y = lerp(smoothCam.y, targetCam.y, 0.045);
    smoothCam.z = lerp(smoothCam.z, targetCam.z, 0.045);

    // Add subtle float
    camera.position.set(
      smoothCam.x + Math.sin(time * 0.12) * 1.5,
      smoothCam.y + Math.cos(time * 0.09) * 0.8,
      smoothCam.z
    );
    camera.lookAt(0, smoothCam.y * 0.3, 0);

    renderer.render(scene, camera);
  }
  animate();

  // ─── RESIZE ─────────────────────────────────────────────────────────────────
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });
})();
