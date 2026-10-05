/* scene3d.js — مجسمات ثري دي لستايل Editorial Grain (Three.js، حتمي بالكامل)
   البيانات بتيجي من window.S3D_CFG اللي بيكتبه build_reel.py من moments.json:
     objects: [{kind, t0, t1, x, y, ...}]   ستيكرات ثري دي فوق الفيديو
     crowd:   {t0, t1, weak, rich}          ناس على قاعدة بالشريط فوق (نوع people)
     map:     {t0, dive, t1}                كرة أرضية ← غوص ← مدينة بتطلع (نوع stack.map)
   كل شي بيترسم من الزمن t بس: S3D.render(t). لا Math.random ولا وقت حقيقي.
   الإحداثيات x,y ببكسل الشاشة (1080×1920). */
(function () {
  const CFG = window.S3D_CFG || {};
  const PAPER = CFG.paper || 0xEFE8DC;
  const W = 540, H = 960;                 // دقة الرسم (بتتكبّر ×2 بالـCSS)
  const canvas = document.getElementById('gl');
  const R = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, preserveDrawingBuffer: true });
  R.setPixelRatio(1); R.setSize(W, H, false);
  R.outputEncoding = THREE.sRGBEncoding;
  R.toneMapping = THREE.ACESFilmicToneMapping; R.toneMappingExposure = 0.92;
  R.setClearColor(0x000000, 0);

  /* ---------- أدوات ---------- */
  let seed = 11;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const io = (x) => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
  const out3 = (x) => 1 - Math.pow(1 - clamp(x), 3);
  const backOut = (x) => { x = clamp(x); const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
  const sine = (x) => -(Math.cos(Math.PI * clamp(x)) - 1) / 2;
  const envl = (t, t0, t1, a = 0.38, b = 0.28) => (t < t0 || t > t1) ? 0 : Math.min(backOut((t - t0) / a), sine((t1 - t) / b));
  const v = (o, k, d) => (o[k] === undefined || o[k] === null) ? d : o[k];

  /* ---------- إضاءة بيئية دافية (للمعدن) ---------- */
  function makeEnv() {
    const s = new THREE.Scene();
    const g = new THREE.SphereGeometry(50, 32, 16);
    const pos = g.attributes.position, cols = [];
    const lo = new THREE.Color(0x4a3c30), hi = new THREE.Color(0xfff1da), c = new THREE.Color();
    for (let i = 0; i < pos.count; i++) { c.lerpColors(lo, hi, clamp((pos.getY(i) / 50 + 1) / 2)); cols.push(c.r, c.g, c.b); }
    g.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
    s.add(new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide })));
    const pm = new THREE.MeshBasicMaterial({ color: 0xffffff });
    [[0, 32, -18, 30, 10], [-34, 12, 24, 14, 22], [36, 6, 20, 10, 18]].forEach(([x, y, z, w, h]) => {
      const p = new THREE.Mesh(new THREE.PlaneGeometry(w, h), pm); p.position.set(x, y, z); p.lookAt(0, 0, 0); s.add(p);
    });
    return new THREE.PMREMGenerator(R).fromScene(s, 0.03).texture;
  }
  const ENV = makeEnv();
  const std = (color, rough = .6, metal = 0, extra = {}) => new THREE.MeshStandardMaterial(Object.assign({ color, roughness: rough, metalness: metal, envMap: ENV, envMapIntensity: metal > .5 ? 1 : .45 }, extra));
  const M = {
    gold: std(0xE3AE47, .26, 1), goldDim: std(0xC99A3E, .35, 1),
    paper: std(0xF1E8D6, .85), paper2: std(0xE3D7C0, .9),
    ink: std(0x2A2522, .45, .25), red: std(CFG.red || 0xC2412D, .45),
    leather: std(0x7A3E24, .5, .05), wood: std(0x8A5A33, .7),
    glass: new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: .05, metalness: 0, transparent: true, opacity: .22, envMap: ENV }),
    steel: std(0x8C8F94, .25, 1),
  };

  /* ---------- مشهد الستيكرات فوق الفيديو ---------- */
  const S = new THREE.Scene(); S.environment = ENV;
  const D = (H * 2 / 2) / Math.tan(THREE.MathUtils.degToRad(15));
  const CAM = new THREE.PerspectiveCamera(30, W / H, 100, 12000); CAM.position.set(0, 0, D); CAM.lookAt(0, 0, 0);
  S.add(new THREE.HemisphereLight(0xfff3e2, 0x6d5d4c, .55));
  const sun = new THREE.DirectionalLight(0xffffff, 1.1); sun.position.set(600, 900, 1400); S.add(sun);
  const P = (x, y) => new THREE.Vector3(x - 540, 960 - y, 0);
  const items = [];
  function add(g, t0, t1, fn) { g.visible = false; S.add(g); items.push({ g, t0, t1, fn }); return g; }

  /* ---------- المجسمات ---------- */
  function makeKey() {
    const g = new THREE.Group();
    const bow = new THREE.Mesh(new THREE.TorusGeometry(42, 13, 16, 48), M.gold); bow.position.x = -95; g.add(bow);
    const inner = new THREE.Mesh(new THREE.TorusGeometry(20, 5, 10, 32), M.gold); inner.position.x = -95; g.add(inner);
    const shaft = new THREE.Mesh(new THREE.CylinderGeometry(10, 10, 170, 20), M.gold); shaft.rotation.z = Math.PI / 2; shaft.position.x = 20; g.add(shaft);
    [[70, 26, 16], [100, 36, 16], [88, 20, 10]].forEach(([x, h, w]) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, 14), M.gold); b.position.set(x, -h / 2 - 6, 0); g.add(b); });
    const tip = new THREE.Mesh(new THREE.SphereGeometry(12, 16, 12), M.gold); tip.position.x = 106; g.add(tip);
    return g;
  }
  function makeCoin(r = 55) {
    const g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 13, 48), M.gold); body.rotation.x = Math.PI / 2; g.add(body);
    [7.5, -7.5].forEach(z => { const ring = new THREE.Mesh(new THREE.TorusGeometry(r * .78, 3, 8, 40), M.goldDim); ring.position.z = z; g.add(ring); });
    const mid = new THREE.Mesh(new THREE.CylinderGeometry(r * .3, r * .3, 15, 24), M.goldDim); mid.rotation.x = Math.PI / 2; g.add(mid);
    return g;
  }
  function makeLens() {
    const g = new THREE.Group();
    g.add(new THREE.Mesh(new THREE.TorusGeometry(72, 13, 18, 48), M.ink));
    g.add(new THREE.Mesh(new THREE.CircleGeometry(66, 40), M.glass));
    const shine = new THREE.Mesh(new THREE.RingGeometry(40, 48, 24, 1, 2.2, 1.0), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: .55, side: THREE.DoubleSide })); shine.position.z = 1; g.add(shine);
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(14, 14, 30, 16), M.ink); neck.position.set(62, -62, 0); neck.rotation.z = Math.PI / 4; g.add(neck);
    const handle = new THREE.Mesh(new THREE.CylinderGeometry(17, 15, 130, 20), M.red); handle.position.set(118, -118, 0); handle.rotation.z = Math.PI / 4; g.add(handle);
    return g;
  }
  function makeCase() {
    const g = new THREE.Group();
    const sh = new THREE.Shape(); const w = 220, h = 150, r = 22;
    sh.moveTo(-w / 2 + r, -h / 2); sh.lineTo(w / 2 - r, -h / 2); sh.quadraticCurveTo(w / 2, -h / 2, w / 2, -h / 2 + r); sh.lineTo(w / 2, h / 2 - r); sh.quadraticCurveTo(w / 2, h / 2, w / 2 - r, h / 2); sh.lineTo(-w / 2 + r, h / 2); sh.quadraticCurveTo(-w / 2, h / 2, -w / 2, h / 2 - r); sh.lineTo(-w / 2, -h / 2 + r); sh.quadraticCurveTo(-w / 2, -h / 2, -w / 2 + r, -h / 2);
    const body = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 64, bevelEnabled: true, bevelSize: 5, bevelThickness: 5, bevelSegments: 3, curveSegments: 8 }), M.leather); body.position.z = -32; g.add(body);
    const strap = new THREE.Mesh(new THREE.BoxGeometry(w + 6, 16, 78), M.ink); strap.position.y = 20; g.add(strap);
    const handle = new THREE.Mesh(new THREE.TorusGeometry(34, 8, 12, 24, Math.PI), M.ink); handle.position.y = h / 2 + 2; g.add(handle);
    [-60, 60].forEach(x => { const c = new THREE.Mesh(new THREE.BoxGeometry(24, 22, 10), M.gold); c.position.set(x, 20, 40); g.add(c); });
    return g;
  }
  function makeMic() {
    const g = new THREE.Group();
    const head = new THREE.Mesh(new THREE.CapsuleGeometry(46, 70, 10, 24), std(0x3a3632, .55, .6)); head.position.y = 60; g.add(head);
    for (let i = 0; i < 5; i++) { const r = new THREE.Mesh(new THREE.TorusGeometry(47, 2, 6, 40), M.steel); r.rotation.x = Math.PI / 2; r.position.y = 20 + i * 22; g.add(r); }
    const band = new THREE.Mesh(new THREE.CylinderGeometry(49, 49, 16, 32), M.gold); g.add(band);
    const body = new THREE.Mesh(new THREE.CylinderGeometry(34, 26, 110, 28), M.ink); body.position.y = -62; g.add(body);
    const yoke = new THREE.Mesh(new THREE.TorusGeometry(66, 7, 10, 32, Math.PI), M.gold); yoke.rotation.z = Math.PI; yoke.position.y = 10; g.add(yoke);
    const post = new THREE.Mesh(new THREE.CylinderGeometry(8, 8, 90, 12), M.gold); post.position.y = -100; g.add(post);
    const base = new THREE.Mesh(new THREE.CylinderGeometry(60, 66, 14, 32), M.ink); base.position.y = -148; g.add(base);
    return g;
  }
  function makeEnvelope() {
    const g = new THREE.Group();
    const kraft = std(0xCDB48A, .85), kraft2 = std(0xBFA27A, .85);
    const bodyG = new THREE.BoxGeometry(240, 150, 8);
    g.add(new THREE.Mesh(bodyG, M.paper));
    g.add(new THREE.LineSegments(new THREE.EdgesGeometry(bodyG), new THREE.LineBasicMaterial({ color: 0x2a2522 })));
    const tri = new THREE.Shape(); tri.moveTo(-120, 0); tri.lineTo(120, 0); tri.lineTo(0, -95); tri.lineTo(-120, 0);
    const flapG = new THREE.ExtrudeGeometry(tri, { depth: 3, bevelEnabled: false });
    const flap = new THREE.Mesh(flapG, kraft); flap.position.set(0, 75, 5); g.add(flap);
    const fl = new THREE.LineSegments(new THREE.EdgesGeometry(flapG), new THREE.LineBasicMaterial({ color: 0x2a2522 })); fl.position.copy(flap.position); g.add(fl);
    const sideL = new THREE.Shape(); sideL.moveTo(-120, 75); sideL.lineTo(-120, -75); sideL.lineTo(-10, 0); sideL.lineTo(-120, 75);
    const sl = new THREE.Mesh(new THREE.ExtrudeGeometry(sideL, { depth: 2, bevelEnabled: false }), kraft2); sl.position.z = 4; g.add(sl);
    const sr = sl.clone(); sr.scale.x = -1; g.add(sr);
    const seal = new THREE.Mesh(new THREE.CylinderGeometry(15, 15, 6, 24), M.red); seal.rotation.x = Math.PI / 2; seal.position.set(0, -18, 11); g.add(seal);
    return g;
  }
  function windowTex(cols, rows, lit) {
    const c = document.createElement('canvas'); c.width = 128; c.height = 256; const x = c.getContext('2d');
    x.fillStyle = '#efe6d4'; x.fillRect(0, 0, 128, 256);
    const cw = 128 / cols, rh = 256 / rows;
    for (let r = 0; r < rows; r++) for (let q = 0; q < cols; q++) {
      x.fillStyle = ((r * 7 + q * 3) % 5 < lit) ? '#f2c66a' : '#3a3430';
      x.fillRect(q * cw + cw * .22, r * rh + rh * .2, cw * .56, rh * .55);
    }
    const t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding; return t;
  }
  function makeTowers() {
    const g = new THREE.Group();
    [[0, 0, 110, 330, 4, 9], [-120, 30, 80, 190, 3, 6], [115, 25, 85, 230, 3, 7]].forEach(([x, z, w, h, c, r]) => {
      const m = new THREE.MeshStandardMaterial({ map: windowTex(c, r, 2), roughness: .7, envMap: ENV });
      const top = std(CFG.red || 0xC2412D, .5);
      const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, w), [m, m, top, top, m, m]);
      b.geometry.translate(0, h / 2, 0); b.position.set(x, 0, z); g.add(b);
    });
    const plate = new THREE.Mesh(new THREE.CylinderGeometry(220, 220, 10, 48), M.paper2); plate.position.y = -5; g.add(plate);
    return g;
  }
  function makeChest() {
    const chest = new THREE.Group();
    const body = new THREE.Mesh(new THREE.BoxGeometry(220, 120, 130), M.wood); body.position.y = 60; chest.add(body);
    [-80, 0, 80].forEach(x => { const b = new THREE.Mesh(new THREE.BoxGeometry(14, 124, 134), M.gold); b.position.set(x, 60, 0); chest.add(b); });
    const lid = new THREE.Group(); lid.position.set(0, 120, -65); chest.add(lid);
    const lc = new THREE.Mesh(new THREE.CylinderGeometry(65, 65, 220, 32, 1, false, 0, Math.PI), M.wood); lc.rotation.z = Math.PI / 2; lc.position.z = 65; lid.add(lc);
    [-80, 0, 80].forEach(x => { const lb = new THREE.Mesh(new THREE.CylinderGeometry(67, 67, 14, 32, 1, false, 0, Math.PI), M.gold); lb.rotation.z = Math.PI / 2; lb.position.set(x, 0, 65); lid.add(lb); });
    const lock = new THREE.Mesh(new THREE.BoxGeometry(34, 40, 10), M.gold); lock.position.set(0, 100, 68); chest.add(lock);
    const pile = new THREE.Group(); for (let i = 0; i < 9; i++) { const c = makeCoin(24); c.rotation.x = -1.2; c.position.set(-70 + (i % 5) * 35, 118 + Math.floor(i / 5) * 14, -30 + (i % 3) * 20); pile.add(c); }
    chest.add(pile);
    const glow = new THREE.PointLight(0xffc860, 0, 600); glow.position.set(0, 220, 40); chest.add(glow);
    chest.userData = { lid, glow };
    return chest;
  }
  function makePlane() {
    const g = new THREE.Group();
    const geo = new THREE.BufferGeometry();
    const vv = [0, 0, 160, -95, 6, -80, 0, -6, -80, 0, 0, 160, 0, -6, -80, 95, 6, -80, 0, 0, 160, 0, -6, -80, 0, -48, -70];
    geo.setAttribute('position', new THREE.Float32BufferAttribute(vv, 3)); geo.computeVertexNormals();
    g.add(new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: 0xF6EFE2, roughness: .8, side: THREE.DoubleSide, envMap: ENV })));
    g.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({ color: 0x2a2522 })));
    return g;
  }
  let globeTex = null;
  function getGlobeTex() {   // قارات مرسومة بدوال حتمية (مش خريطة حقيقية لأي بلد)
    if (globeTex) return globeTex;
    const c = document.createElement('canvas'); c.width = 512; c.height = 256; const x = c.getContext('2d');
    const img = x.createImageData(512, 256);
    for (let j = 0; j < 256; j++) for (let i = 0; i < 512; i++) {
      const lon = (i / 512) * Math.PI * 2 - Math.PI, lat = Math.PI / 2 - (j / 256) * Math.PI;
      const vv = Math.sin(lon * 2.1 + 1.3) * Math.cos(lat * 3.2 - .4) + .55 * Math.sin(lon * 4.7 - lat * 2.3) + .35 * Math.cos(lon * 7.3 + lat * 5.1);
      const k = (j * 512 + i) * 4, land = vv > .32, coast = Math.abs(vv - .32) < .035;
      const col = coast ? [42, 37, 34] : land ? [236, 224, 200] : [47, 82, 96];
      img.data[k] = col[0]; img.data[k + 1] = col[1]; img.data[k + 2] = col[2]; img.data[k + 3] = 255;
    }
    x.putImageData(img, 0, 0);
    globeTex = new THREE.CanvasTexture(c); globeTex.encoding = THREE.sRGBEncoding; return globeTex;
  }
  function makeGlobe(r, seg) {
    const g = new THREE.Group();
    g.add(new THREE.Mesh(new THREE.SphereGeometry(r, seg, seg / 2), new THREE.MeshStandardMaterial({ map: getGlobeTex(), roughness: .8, envMap: ENV, envMapIntensity: .4 })));
    const ring = new THREE.Mesh(new THREE.TorusGeometry(r * 1.32, r * .025, 8, 80), M.gold); ring.rotation.x = Math.PI / 2.3; g.add(ring);
    return g;
  }

  /* ---------- الحركات حسب النوع (كل الأوقات نسبة لـ t0 أو أوقات مطلقة من moments.json) ---------- */
  const KINDS = {
    key(o) {   // بينزلق من اليمين ويلف
      const x = v(o, 'x', 810), y = v(o, 'y', 1165), s = v(o, 'scale', 1.6);
      add(makeKey(), o.t0, o.t1, (g, t, lt, e) => {
        const k = out3(lt / .55);
        g.position.copy(P(lerp(x + 310, x, k), y + Math.sin(lt * 3) * 10));
        g.rotation.set(.25 + Math.sin(lt * 2) * .1, lt * 2.6, -.35 + Math.sin(lt * 1.7) * .08);
        g.scale.setScalar(s * e);
      });
    },
    coins(o) { // 5 عملات بتنفجر من نقطة
      const x = v(o, 'x', 540), y = v(o, 'y', 1230), s = v(o, 'scale', 1.35);
      [[-330, -170], [-170, -260], [10, -300], [190, -250], [340, -160]].forEach(([dx, dy], i) => {
        add(makeCoin(64), o.t0 + i * .05, o.t1, (g, t, lt, e) => {
          const k = backOut((t - o.t0 - i * .05) / .55);
          g.position.copy(P(x + dx * k, y + dy * k + Math.sin(lt * 4 + i) * 8));
          g.rotation.set(.3, lt * 6 + i, .2 * Math.sin(lt * 3 + i));
          g.scale.setScalar(s * e);
        });
      });
    },
    lens(o) {  // عدسة بتدوّر: sweep (من نقطة لنقطة) أو orbit (بتلف حوالين نقطة) — fall: وقت الوقعة، lift: وقت الطلعة
      const s = v(o, 'scale', 1.5);
      if (v(o, 'motion', 'sweep') === 'orbit') {
        const x = v(o, 'x', 820), y = v(o, 'y', 1050);
        add(makeLens(), o.t0, o.t1, (g, t, lt, e) => {
          const fall = o.fall ? clamp((t - o.fall) / .55) : 0;
          g.position.copy(P(x + Math.sin(lt * 2.4) * 60 + fall * 60, y + Math.cos(lt * 2.4) * 30 + fall * fall * 700));
          g.rotation.set(.15, -.3 + Math.sin(lt * 2) * .2, Math.sin(lt * 3) * .12 + fall * 2.2);
          g.scale.setScalar(s * (fall > 0 ? 1 : e));
        });
      } else {
        const [x0, y0] = v(o, 'from', [930, 1080]), [x1] = v(o, 'to', [300, 1080]), dur = v(o, 'dur', 1.45);
        add(makeLens(), o.t0, o.t1, (g, t, lt, e) => {
          const k = sine(lt / dur), lift = o.lift ? out3((t - o.lift) / .4) : 0;
          g.position.copy(P(lerp(x0, x1, k) + lift * 120, y0 + Math.sin(lt * 5) * 14 - lift * 150));
          g.rotation.set(.15, -.35 + Math.sin(lt * 2) * .15, Math.sin(lt * 3) * .12);
          g.scale.setScalar(s * e);
        });
      }
    },
    case(o) {
      const x = v(o, 'x', 300), y = v(o, 'y', 1110), s = v(o, 'scale', 1.45);
      add(makeCase(), o.t0, o.t1, (g, t, lt, e) => { g.position.copy(P(x, y)); g.rotation.set(.2, -.5 + lt * .8, 0); g.scale.setScalar(s * e); });
    },
    mic(o) {
      const x = v(o, 'x', 870), y = v(o, 'y', 990), s = v(o, 'scale', 1.45);
      add(makeMic(), o.t0, o.t1, (g, t, lt, e) => {
        g.position.copy(P(x, y + Math.sin(lt * 2) * 8));
        g.rotation.set(.12, .5 + Math.sin(lt * 1.4) * .45, Math.sin(lt * 1.8) * .05);
        g.scale.setScalar(s * e);
      });
    },
    envelope(o) {  // drop: بينزل من فوق وبيطير لفوق بالآخر · across: بيقطع الشاشة
      const s = v(o, 'scale', o.motion === 'across' ? 1.35 : 1.45);
      if (o.motion === 'across') {
        const y = v(o, 'y', 1130), dur = v(o, 'dur', 1.6);
        add(makeEnvelope(), o.t0, o.t1, (g, t, lt) => {
          const k = sine(lt / dur);
          g.position.copy(P(lerp(1150, -120, k), y - Math.sin(k * Math.PI) * 110));
          g.rotation.set(.3, -.6 + k * 1.2, lerp(-.25, .25, k) + Math.sin(lt * 6) * .06);
          g.scale.setScalar(s);
        });
      } else {
        const x = v(o, 'x', 215), y = v(o, 'y', 250);
        add(makeEnvelope(), o.t0, o.t1, (g, t, lt, e) => {
          const k = out3(lt / .8), up = clamp((t - (o.t1 - .35)) / .35);
          g.position.copy(P(x, lerp(-80, y, k) - up * up * 500 + Math.sin(lt * 2.2) * 10));
          g.rotation.set(.25 + Math.sin(lt * 1.5) * .12, Math.sin(lt * 1.2) * .5, lerp(.5, -.12, k));
          g.scale.setScalar(Math.max(e, up > 0 ? 1 : 0) * s);
        });
      }
    },
    towers(o) {  // ثلاث بنايات بتطلع
      const x = v(o, 'x', 235), y = v(o, 'y', 1268), s = v(o, 'scale', 1.25);
      add(makeTowers(), o.t0, o.t1, (g, t, lt, e) => {
        g.position.copy(P(x, y)); g.rotation.set(.3, -.6 + lt * .35, 0); g.scale.setScalar(s * Math.max(.001, e));
        g.children.forEach((b, i) => { if (i < 3) b.scale.y = Math.max(.01, out3((t - o.t0 - .05 - i * .12) / .6)); });
      });
    },
    chest(o) {   // صندوق كنز بينفتح عند open
      const x = v(o, 'x', 300), y = v(o, 'y', 712), s = v(o, 'scale', .95), open = v(o, 'open', o.t0 + .3);
      add(makeChest(), o.t0, o.t1, (g, t, lt, e) => {
        g.position.copy(P(x, y)); g.rotation.set(.32, .55 + Math.sin(lt * 1.3) * .12, 0); g.scale.setScalar(s * e);
        const k = out3((t - open) / .5); g.userData.lid.rotation.x = -1.35 * k; g.userData.glow.intensity = 2.2 * k;
      });
    },
    plane(o) {   // طيارة ورق بتقطع من اليمين لليسار
      const y = v(o, 'y', 520), s = v(o, 'scale', 1.6), dur = v(o, 'dur', 1.3);
      add(makePlane(), o.t0, o.t1, (g, t, lt) => {
        const k = sine(lt / dur);
        g.position.copy(P(lerp(1180, -160, k), y - Math.sin(k * Math.PI) * 40)); g.position.z = Math.sin(k * Math.PI) * 300;
        g.rotation.set(-.15 + Math.sin(k * Math.PI) * .2, -Math.PI / 2 + .25, -.5 + k * .3);
        g.scale.setScalar(s);
      });
    },
    globe(o) {   // كرة صغيرة بتلف وبتوقف فجأة عند stop
      const x = v(o, 'x', 860), y = v(o, 'y', 1060), s = v(o, 'scale', 1.4), stop = v(o, 'stop', o.t0 + .6);
      add(makeGlobe(105, 48), o.t0, o.t1, (g, t, lt, e) => {
        g.position.copy(P(x, y));
        const spin = t < stop ? (t - o.t0) * 3 : (stop - o.t0) * 3 + Math.sin((t - stop) * 30) * .06 * (1 - clamp((t - stop - .16) / .4));
        g.rotation.set(.35, spin, .15); g.scale.setScalar(s * e);
      });
    },
  };
  (CFG.objects || []).forEach(o => { if (KINDS[o.kind]) KINDS[o.kind](o); else console.warn('scene3d: نوع مش معروف', o.kind); });

  /* ---------- الناس (نوع people): قاعدة عليها ناس — بيبهتوا عند weak وبيصيروا ذهب عند rich ---------- */
  const CR = CFG.crowd;
  if (CR) {
    const pawnMat = std(0xD8CCB4, .6, 0);
    const crowd = new THREE.Group();
    const prof = [[0, 0], [38, 0], [38, 8], [26, 18], [20, 60], [26, 72], [16, 84], [0, 86]];
    const lat = new THREE.LatheGeometry(prof.map(([x, y]) => new THREE.Vector2(x, y)), 28);
    const floor = new THREE.Mesh(new THREE.CylinderGeometry(470, 470, 12, 64), M.paper2); floor.position.y = -8; crowd.add(floor);
    const rim = new THREE.Mesh(new THREE.TorusGeometry(470, 4, 8, 80), M.ink); rim.rotation.x = Math.PI / 2; rim.position.y = -2; crowd.add(rim);
    const pawns = [], coins = [];
    [[-300, 40], [-200, -60], [-100, 70], [0, -40], [100, 80], [200, -70], [300, 30]].forEach(([x, z]) => {
      const p = new THREE.Group(); p.add(new THREE.Mesh(lat, pawnMat));
      const head = new THREE.Mesh(new THREE.SphereGeometry(24, 24, 16), pawnMat); head.position.y = 108; p.add(head);
      p.position.set(x, 0, z); p.scale.setScalar(1.25); crowd.add(p); pawns.push(p);
      const c = makeCoin(26); c.position.set(x, 400, z); crowd.add(c); coins.push(c);
    });
    const beam = new THREE.Mesh(new THREE.CylinderGeometry(140, 420, 700, 40, 1, true), new THREE.MeshBasicMaterial({ color: 0xffb340, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending }));
    beam.position.y = 330; crowd.add(beam);
    const grey = new THREE.Color(0x8f897f), base = new THREE.Color(0xD8CCB4), goldC = new THREE.Color(0xE3AE47);
    const weakT = v(CR, 'weak', CR.t0 + 2), richT = v(CR, 'rich', CR.t1 - 1.1);
    add(crowd, CR.t0, CR.t1, (g, t, lt, e) => {
      g.position.copy(P(540, v(CR, 'y', 455))); g.rotation.set(.38, -.5 + lt * .16, 0); g.scale.setScalar(.92 * Math.max(.001, e));
      const weak = clamp((t - weakT) / .5), rich = clamp((t - richT) / .6);
      pawnMat.color.copy(base).lerp(grey, weak * (1 - rich)).lerp(goldC, rich);
      pawnMat.metalness = rich * .9; pawnMat.roughness = lerp(.6, .3, rich);
      pawns.forEach((p, i) => {
        p.scale.set(1.25, 1.25 * (1 - .14 * weak * (1 - rich)), 1.25);
        const j = richT + .4 + i * .05;
        p.position.y = Math.max(0, Math.sin((t - j) * 9) * 18 * clamp((t - j) / .1) * (1 - clamp((t - richT - .8) / .2)));
      });
      coins.forEach((c, i) => { const k = clamp((t - richT - .05 - i * .06) / .45); c.visible = k > 0; c.position.y = lerp(520, 150, k * k); c.rotation.set(Math.PI / 2 * .2, t * 6 + i, 0); });
      beam.material.opacity = .05 * clamp((t - richT + .05) / .3) * sine((CR.t1 - t) / .3);
    });
  }

  /* ---------- الخريطة (stack.map): كرة أرضية ← غوص ← مدينة: مباني، دبابيس، مصاري ---------- */
  const MP = CFG.map;
  let MS = null, MC = null, renderMap = null;
  if (MP) {
    const M0 = MP.t0, MD = MP.dive, M1 = MP.t1;
    MS = new THREE.Scene(); MS.background = new THREE.Color(PAPER); MS.fog = new THREE.Fog(PAPER, 2600, 7200); MS.environment = ENV;
    MS.add(new THREE.HemisphereLight(0xfff4e4, 0x6f604f, .5));
    const msun = new THREE.DirectionalLight(0xffffff, 1.0); msun.position.set(900, 1600, 700); MS.add(msun);
    MC = new THREE.PerspectiveCamera(38, W / H, 5, 9000);
    const bigGlobe = makeGlobe(200, 96); MS.add(bigGlobe);
    for (let i = -2; i <= 2; i++) { const la = i * .45; const r = 201 * Math.cos(la); const tt = new THREE.Mesh(new THREE.TorusGeometry(r, .9, 6, 90), M.ink); tt.rotation.x = Math.PI / 2; tt.position.y = 201 * Math.sin(la); bigGlobe.add(tt); }
    const city = new THREE.Group(); city.visible = false; MS.add(city);
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(9000, 9000), std(0xCDBB9A, .95)); ground.rotation.x = -Math.PI / 2; ground.position.y = -1; city.add(ground);
    const roadMat = std(0x2E2925, .85);
    const B = 230, G = 46, N = 5, span = (2 * N + 1) * (B + G);
    for (let i = -N; i <= N + 1; i++) {
      const p = i * (B + G) - (B + G) / 2;
      const r1 = new THREE.Mesh(new THREE.BoxGeometry(span, 2, 24), roadMat); r1.position.set(0, 1, p); city.add(r1);
      const r2 = new THREE.Mesh(new THREE.BoxGeometry(24, 2, span), roadMat); r2.position.set(p, 1, 0); city.add(r2);
    }
    const buildings = [], pins = [], stacks = [], trees = [];
    const parkMat = std(0xA9B47E, .95), lotMat = std(0xEFE5D1, .9), lot2 = std(0xE2CDB0, .9);
    const bMats = [0, 1, 2, 3].map(k => new THREE.MeshStandardMaterial({ map: windowTex(3 + (k % 2), 6 + k, 2), roughness: .75, envMap: ENV }));
    const roofMat = std(0x3A332E, .7), roofRed = std(CFG.red || 0xC2412D, .55);
    seed = 29;
    for (let i = -N; i <= N; i++) for (let j = -N; j <= N; j++) {
      const cx = i * (B + G), cz = j * (B + G), d = Math.hypot(i, j);
      const kind = (Math.abs(i * 3 + j * 5) % 7 === 0) ? 'park' : 'lot';
      const lot = new THREE.Mesh(new THREE.BoxGeometry(B, 4, B), kind === 'park' ? parkMat : ((i + j) % 2 ? lotMat : lot2)); lot.position.set(cx, 2, cz); city.add(lot);
      if (kind === 'park') {
        for (let q = 0; q < 5; q++) { const tr = new THREE.Group(); const c = new THREE.Mesh(new THREE.ConeGeometry(28, 76, 10), std(0x4F6B3A, .85)); c.position.y = 55; tr.add(c); const s = new THREE.Mesh(new THREE.CylinderGeometry(5, 6, 22, 6), M.wood); s.position.y = 11; tr.add(s); tr.position.set(cx - 70 + (q % 3) * 70, 4, cz - 50 + Math.floor(q / 3) * 100); city.add(tr); trees.push({ o: tr, d }); }
        continue;
      }
      const nb = 1 + Math.floor(rnd() * 3);
      for (let q = 0; q < nb; q++) {
        const w = 60 + rnd() * 50, h = (60 + rnd() * 240) * (1.25 - Math.min(1, d / 7)) + 30;
        const m = bMats[Math.floor(rnd() * 4)];
        const geo = new THREE.BoxGeometry(w, h, w); geo.translate(0, h / 2, 0);
        const top = rnd() < .32 ? roofRed : roofMat;
        const b = new THREE.Mesh(geo, [m, m, top, top, m, m]);
        b.position.set(cx + (q - (nb - 1) / 2) * (B / nb) * .9, 4, cz + (rnd() - .5) * 70);
        b.scale.y = .01; city.add(b); buildings.push({ o: b, d: d + rnd() * .6 });
      }
      if (rnd() < .2 && d < 4) {
        const pin = new THREE.Group(); const head = new THREE.Mesh(new THREE.SphereGeometry(30, 20, 14), M.red); head.position.y = 120; pin.add(head);
        const cone = new THREE.Mesh(new THREE.ConeGeometry(16, 90, 14), M.red); cone.rotation.x = Math.PI; cone.position.y = 70; pin.add(cone);
        const dot = new THREE.Mesh(new THREE.SphereGeometry(10, 10, 8), M.paper); dot.position.set(0, 120, 28); pin.add(dot);
        pin.position.set(cx, 300, cz); city.add(pin); pins.push({ o: pin, d });
      } else if (rnd() < .35 && d < 4.5) {
        const st = new THREE.Group(); const n = 5 + Math.floor(rnd() * 7);
        for (let k = 0; k < n; k++) { const c = new THREE.Mesh(new THREE.CylinderGeometry(30, 30, 9, 28), k % 2 ? M.gold : M.goldDim); c.position.y = 6 + k * 10; c.position.x = Math.sin(k * 1.7) * 2; st.add(c); }
        st.position.set(cx + 60, 4, cz - 60); st.scale.y = .01; city.add(st); stacks.push({ o: st, d });
      }
    }
    const flyCoins = []; for (let i = 0; i < 10; i++) { const c = makeCoin(34); city.add(c); flyCoins.push(c); c.visible = false; }
    const camPath = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0, 1650, 1500), new THREE.Vector3(520, 900, 1050), new THREE.Vector3(160, 560, 700),
      new THREE.Vector3(-380, 620, 560), new THREE.Vector3(-260, 1350, 1250), new THREE.Vector3(0, 2100, 1900)]);
    const lookPath = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0, 0, 0), new THREE.Vector3(60, 40, 0), new THREE.Vector3(-40, 60, -60),
      new THREE.Vector3(-80, 60, -40), new THREE.Vector3(0, 40, 0), new THREE.Vector3(0, 0, -100)]);
    const tPin = v(MP, 'pins', MD + .22), tMoney = v(MP, 'money', MD + .67);
    renderMap = function (t) {
      if (t < MD) {
        bigGlobe.visible = true; city.visible = false;
        bigGlobe.rotation.set(.3, (t - M0) * .55 + 1.2, 0);
        const dive = io((t - (MD - .43)) / .43);
        const dist = lerp(lerp(1650, 1180, sine((t - M0) / 1.35)), 250, dive);
        MC.position.set(0, lerp(120, 30, dive), dist); MC.lookAt(0, 0, 0);
      } else {
        bigGlobe.visible = false; city.visible = true;
        const u = sine((t - MD) / (M1 - MD));
        MC.position.copy(camPath.getPoint(u)); MC.lookAt(lookPath.getPoint(u));
        buildings.forEach(({ o, d }) => { o.scale.y = Math.max(.01, backOut((t - MD - .05 - d * .09) / .5)); });
        trees.forEach(({ o, d }) => { o.scale.setScalar(Math.max(.01, backOut((t - MD - .1 - d * .08) / .4))); });
        pins.forEach(({ o, d }) => {
          const k = clamp((t - tPin - d * .08) / .35);
          o.position.y = lerp(420, 4, k * k) + (k >= 1 ? Math.max(0, Math.sin((t - tPin - .35 - d * .08) * 12) * 18 * (1 - clamp((t - tPin - .5 - d * .08) / .4))) : 0);
          o.visible = k > 0; o.rotation.y = t * 1.5;
        });
        stacks.forEach(({ o, d }) => { o.scale.y = Math.max(.01, backOut((t - tMoney - d * .06) / .45)); });
        flyCoins.forEach((c, i) => {
          const s = stacks[i % Math.max(1, stacks.length)]; const k = clamp((t - tMoney - .05 - i * .07) / .9);
          c.visible = k > 0 && k < 1 && !!s; if (!s) return;
          c.position.set(s.o.position.x, 120 + Math.sin(k * Math.PI) * 260, s.o.position.z); c.rotation.set(.4, t * 7 + i, 0);
        });
      }
      R.setClearColor(PAPER, 1); R.render(MS, MC);
    };
  }

  /* ---------- الرسم ---------- */
  let wasEmpty = false;
  function render(t) {
    if (MP && t >= MP.t0 && t <= MP.t1) { renderMap(t); wasEmpty = false; return; }
    let any = false;
    items.forEach(it => {
      if (t >= it.t0 && t <= it.t1) { it.g.visible = true; it.fn(it.g, t, t - it.t0, envl(t, it.t0, it.t1)); any = true; }
      else it.g.visible = false;
    });
    R.setClearColor(0x000000, 0);
    if (any) { R.render(S, CAM); wasEmpty = false; }
    else if (!wasEmpty) { R.clear(); wasEmpty = true; }
  }
  window.S3D = { render, ready: () => true };
})();
