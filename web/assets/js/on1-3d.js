/*
 * Orman Nöbetçisi ON-1 — Prosedürel 3B ürün modeli ve görüntüleyici
 * Birim: 1 = 1 cm. Ön yüz = +Z (termal pencere), gövde tabanı y = 0.
 * Klasik script (file:// altında da çalışsın diye ES modülü değil).
 * Kullanım: ON1Viewer(THREE, addons, containerEl, { view, interactive, labels })
 */
(function () {
  'use strict';

  const D2R = Math.PI / 180;

  // ---------- Prosedürel dokular ----------
  function canvasTex(THREE, w, h, draw, opts) {
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    const g = c.getContext('2d');
    draw(g, w, h);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 8;
    if (opts && opts.repeat) {
      t.wrapS = t.wrapT = THREE.RepeatWrapping;
      t.repeat.set(opts.repeat[0], opts.repeat[1]);
    }
    return t;
  }

  function rng(seed) {
    let s = seed >>> 0;
    return function () {
      s = (s * 1664525 + 1013904223) >>> 0;
      return s / 4294967296;
    };
  }

  function barkTexture(THREE) {
    return canvasTex(THREE, 512, 1024, (g, w, h) => {
      const r = rng(7);
      g.fillStyle = '#4a3a2c';
      g.fillRect(0, 0, w, h);
      for (let i = 0; i < 900; i++) {
        const x = r() * w, y = r() * h, len = 40 + r() * 220, wid = 2 + r() * 9;
        const l = 18 + r() * 26;
        g.fillStyle = `hsl(${24 + r() * 10}, ${18 + r() * 14}%, ${l}%)`;
        g.globalAlpha = 0.35 + r() * 0.5;
        const rot = (r() - 0.5) * 0.08;
        for (const dx of [-w, 0, w]) for (const dy of [-h, 0, h]) {
          g.beginPath(); g.ellipse(x + dx, y + dy, wid, len, rot, 0, Math.PI * 2); g.fill();
        }
      }
      g.globalAlpha = 1;
      // derin çatlaklar
      for (let i = 0; i < 70; i++) {
        const x0 = r() * w, y0 = r() * h, lw = 1.5 + r() * 3.5;
        const pts = [[x0, y0]];
        for (let k = 0; k < 8; k++) { const [px, py] = pts[pts.length - 1]; pts.push([px + (r() - 0.5) * 14, py + 20 + r() * 30]); }
        g.strokeStyle = 'rgba(20,14,10,0.75)'; g.lineWidth = lw;
        for (const dx of [-w, 0, w]) for (const dy of [-h, 0, h]) {
          g.beginPath(); pts.forEach(([px, py], i) => (i ? g.lineTo(px + dx, py + dy) : g.moveTo(px + dx, py + dy))); g.stroke();
        }
      }
      // yosun lekeleri
      for (let i = 0; i < 40; i++) {
        g.fillStyle = `rgba(${70 + r() * 30},${90 + r() * 30},${50 + r() * 20},${0.05 + r() * 0.08})`;
        g.beginPath(); g.arc(r() * w, r() * h, 6 + r() * 30, 0, Math.PI * 2); g.fill();
      }
    }, { repeat: [3, 4] });
  }

  function solarTexture(THREE) {
    return canvasTex(THREE, 1100, 900, (g, w, h) => {
      g.fillStyle = '#0d1420';
      g.fillRect(0, 0, w, h);
      const cols = 4, rows = 3, m = 34, gap = 10;
      const cw = (w - 2 * m - (cols - 1) * gap) / cols, ch = (h - 2 * m - (rows - 1) * gap) / rows;
      for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
        const x = m + i * (cw + gap), y = m + j * (ch + gap);
        const grd = g.createLinearGradient(x, y, x + cw, y + ch);
        grd.addColorStop(0, '#1b2b4a'); grd.addColorStop(0.5, '#14223d'); grd.addColorStop(1, '#1a2947');
        g.fillStyle = grd; g.fillRect(x, y, cw, ch);
        g.strokeStyle = 'rgba(190,200,215,0.18)'; g.lineWidth = 1;
        for (let k = 1; k < 26; k++) { const yy = y + (ch * k) / 26; g.beginPath(); g.moveTo(x, yy); g.lineTo(x + cw, yy); g.stroke(); }
        g.fillStyle = 'rgba(205,212,222,0.85)';
        g.fillRect(x + cw * 0.3 - 3, y, 6, ch); g.fillRect(x + cw * 0.7 - 3, y, 6, ch);
      }
      g.fillStyle = 'rgba(205,212,222,0.75)';
      g.fillRect(m, h - m + 8, w - 2 * m, 8);
      g.fillStyle = 'rgba(255,255,255,0.55)';
      g.font = '600 20px sans-serif';
      g.fillText('ON-1  ·  6V 3W MONO ETFE', m, m - 10);
    });
  }

  function labelTexture(THREE) {
    return canvasTex(THREE, 1400, 560, (g, w, h) => {
      g.fillStyle = '#f7f5ef'; g.fillRect(0, 0, w, h);
      g.fillStyle = '#1f4d3a'; g.fillRect(0, 0, w, 150);
      g.fillStyle = '#e4572e'; g.fillRect(0, 150, w, 16);
      g.fillStyle = '#ffffff';
      g.font = '800 92px Archivo, Arial, sans-serif';
      g.textAlign = 'center';
      g.fillText('ORMAN NÖBETÇİSİ', w / 2, 108);
      g.fillStyle = '#1b1f1d';
      g.font = '700 70px Archivo, Arial, sans-serif';
      g.fillText('ON-1', w / 2, 262);
      g.font = '500 40px Arial, sans-serif';
      g.fillStyle = '#3c4440';
      g.fillText('Erken Yangın Algılama • SMS • Işıklı Alarm', w / 2, 330);
      // mıknatıs test noktası
      g.strokeStyle = '#e4572e'; g.lineWidth = 8;
      g.beginPath(); g.arc(w / 2 - 330, 440, 46, 0, Math.PI * 2); g.stroke();
      g.fillStyle = '#e4572e'; g.font = '800 44px Arial'; g.fillText('N', w / 2 - 330, 456);
      g.fillStyle = '#3c4440'; g.font = '500 34px Arial'; g.textAlign = 'left';
      g.fillText('TEST: mıknatısı 3 sn tutun', w / 2 - 265, 452);
      g.textAlign = 'right'; g.font = '600 32px monospace';
      g.fillText('ID: ON1-0007', w - 60, 520);
      // QR benzeri desen
      const r = rng(3), qx = 70, qy = 380, s = 12;
      g.fillStyle = '#1b1f1d';
      for (let i = 0; i < 12; i++) for (let j = 0; j < 12; j++) if (r() > 0.5) g.fillRect(qx + i * s, qy + j * s, s, s);
      [[0, 0], [8, 0], [0, 8]].forEach(([a, b]) => {
        g.fillRect(qx + a * s, qy + b * s, 4 * s, 4 * s);
        g.fillStyle = '#f7f5ef'; g.fillRect(qx + a * s + s, qy + b * s + s, 2 * s, 2 * s); g.fillStyle = '#1b1f1d';
      });
    });
  }

  function pcbTexture(THREE) {
    return canvasTex(THREE, 780, 580, (g, w, h) => {
      g.fillStyle = '#0f5a3a'; g.fillRect(0, 0, w, h);
      const r = rng(11);
      g.strokeStyle = 'rgba(180,220,170,0.35)'; g.lineWidth = 3;
      for (let i = 0; i < 90; i++) {
        let x = r() * w, y = r() * h; g.beginPath(); g.moveTo(x, y);
        for (let k = 0; k < 3; k++) { if (r() > 0.5) x += (r() - 0.5) * 200; else y += (r() - 0.5) * 200; g.lineTo(x, y); }
        g.stroke();
      }
      g.fillStyle = '#d9c27a';
      for (let i = 0; i < 160; i++) g.fillRect(r() * w, r() * h, 6, 6);
      g.fillStyle = '#f2f2f2'; g.font = '700 26px monospace';
      g.fillText('ON1-MB Rev A', 24, h - 24);
      g.font = '600 18px monospace'; g.fillText('U1  U2  U3  Q1  J6', 24, 34);
      g.strokeStyle = '#f2f2f2'; g.lineWidth = 2; g.strokeRect(6, 6, w - 12, h - 12);
    });
  }

  function grilleTexture(THREE) {
    return canvasTex(THREE, 256, 256, (g, w, h) => {
      g.fillStyle = '#1a1a1a'; g.fillRect(0, 0, w, h);
      g.fillStyle = '#050505';
      for (let i = 0; i < 9; i++) for (let j = 0; j < 9; j++) {
        const x = 20 + i * 27, y = 20 + j * 27;
        if ((x - 128) ** 2 + (y - 128) ** 2 < 110 ** 2) { g.beginPath(); g.arc(x, y, 7, 0, Math.PI * 2); g.fill(); }
      }
    });
  }

  function meshTexture(THREE) {
    return canvasTex(THREE, 128, 128, (g, w, h) => {
      g.fillStyle = 'rgba(0,0,0,0)'; g.clearRect(0, 0, w, h);
      g.strokeStyle = 'rgba(200,205,210,0.95)'; g.lineWidth = 2;
      for (let i = 0; i <= w; i += 10) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, h); g.stroke(); g.beginPath(); g.moveTo(0, i); g.lineTo(w, i); g.stroke(); }
    });
  }

  // ---------- Model ----------
  function buildON1(THREE, opts) {
    opts = opts || {};
    const R = 7.65, H = 17.8;
    const root = new THREE.Group();
    const parts = {};
    const labels = [];
    const ledMats = [];
    const alarmLights = [];

    const M = {
      paint: new THREE.MeshPhysicalMaterial({ color: 0xf2f1ec, roughness: 0.38, metalness: 0.15, clearcoat: 0.5, clearcoatRoughness: 0.3 }),
      tin: new THREE.MeshStandardMaterial({ color: 0xd9dcdf, roughness: 0.25, metalness: 0.95 }),
      alu: new THREE.MeshStandardMaterial({ color: 0xc4c8cc, roughness: 0.35, metalness: 0.9 }),
      steel: new THREE.MeshStandardMaterial({ color: 0xb8bcc0, roughness: 0.22, metalness: 1.0 }),
      black: new THREE.MeshStandardMaterial({ color: 0x151616, roughness: 0.55, metalness: 0.1 }),
      rubber: new THREE.MeshStandardMaterial({ color: 0x1b1c1c, roughness: 0.9, metalness: 0.0 }),
      green: new THREE.MeshStandardMaterial({ color: 0x1f4d3a, roughness: 0.5, metalness: 0.1 }),
      orange: new THREE.MeshStandardMaterial({ color: 0xe4572e, roughness: 0.45, metalness: 0.1 }),
      hdpe: new THREE.MeshPhysicalMaterial({ color: 0xf0f0ea, roughness: 0.6, transmission: 0.35, thickness: 0.2, transparent: true, opacity: 0.92 }),
      pc: new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.08, transmission: 0.92, thickness: 0.4, ior: 1.58, transparent: true, opacity: 0.55 }),
      asa: new THREE.MeshStandardMaterial({ color: 0x2d3331, roughness: 0.7, metalness: 0.0 }),
      cellBlue: new THREE.MeshStandardMaterial({ color: 0x2a5bd7, roughness: 0.35, metalness: 0.2 }),
      shield: new THREE.MeshStandardMaterial({ color: 0xcfd3d6, roughness: 0.2, metalness: 1.0 }),
      silica: new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.95 }),
    };

    const add = (parent, geo, mat, pos, rot, name) => {
      const m = new THREE.Mesh(geo, mat);
      if (pos) m.position.set(pos[0], pos[1], pos[2]);
      if (rot) m.rotation.set(rot[0], rot[1], rot[2]);
      m.castShadow = true; m.receiveShadow = true;
      if (name) m.name = name;
      parent.add(m);
      return m;
    };
    const onWall = (thetaDeg, y, out) => {
      const t = thetaDeg * D2R, r = R + (out || 0);
      return [r * Math.sin(t), y, r * Math.cos(t)];
    };

    // ===== GÖVDE =====
    const body = new THREE.Group(); body.name = 'body'; root.add(body); parts.body = body;
    const bodyFull = add(body, new THREE.CylinderGeometry(R, R, H, 128, 1, true), M.paint, [0, H / 2, 0]);
    bodyFull.material = M.paint.clone(); bodyFull.material.side = THREE.DoubleSide;
    // kesit (patlatılmış görünüm için 270°)
    const bodyCut = add(body, new THREE.CylinderGeometry(R, R, H, 128, 1, true, 135 * D2R, 270 * D2R), bodyFull.material, [0, H / 2, 0]);
    bodyCut.visible = false;
    parts.bodyFull = bodyFull; parts.bodyCut = bodyCut;
    // iç köpük (sadece kesitte görünür)
    const foam = add(body, new THREE.CylinderGeometry(R - 0.5, R - 0.5, H - 0.6, 96, 1, true, 135 * D2R, 270 * D2R),
      new THREE.MeshStandardMaterial({ color: 0xb9bec2, roughness: 0.4, metalness: 0.6, side: THREE.DoubleSide }), [0, H / 2, 0]);
    foam.visible = false; parts.foam = foam;
    // teneke boncukları (nervürler) ve kenar kıvrımları
    [3.2, 14.6].forEach((y) => {
      const ring = add(body, new THREE.TorusGeometry(R + 0.02, 0.16, 12, 128), M.paint, [0, y, 0], [Math.PI / 2, 0, 0]);
      ring.userData.bead = true;
    });
    add(body, new THREE.TorusGeometry(R + 0.05, 0.28, 16, 128), M.tin, [0, 0.15, 0], [Math.PI / 2, 0, 0]);
    add(body, new THREE.CircleGeometry(R, 96), M.paint, [0, 0.02, 0], [Math.PI / 2, 0, 0]);
    // etiket
    const lblW = 100 * D2R;
    add(body, new THREE.CylinderGeometry(R + 0.03, R + 0.03, 6.2, 64, 1, true, -lblW / 2, lblW),
      new THREE.MeshStandardMaterial({ map: labelTexture(THREE), roughness: 0.55, metalness: 0.0 }), [0, 7.6, 0]);

    // termal pencere (AMG8833) — 35° aşağı bakış
    const win = new THREE.Group(); win.position.set(0, 12.9, R - 0.1); win.rotation.x = 35 * D2R; body.add(win);
    const boss = add(win, new THREE.CylinderGeometry(2.0, 2.2, 1.6, 48), M.paint, [0, 0, 0.8], [Math.PI / 2, 0, 0]);
    add(win, new THREE.TorusGeometry(1.6, 0.18, 12, 48), M.steel, [0, 0, 1.62]);
    add(win, new THREE.CircleGeometry(1.55, 48), M.hdpe, [0, 0, 1.6]);
    const meshMat = new THREE.MeshStandardMaterial({ map: meshTexture(THREE), transparent: true, metalness: 1, roughness: 0.3, alphaTest: 0.3 });
    add(win, new THREE.CircleGeometry(1.55, 48), meshMat, [0, 0, 1.68]);
    const hoodShape = new THREE.Shape();
    hoodShape.absarc(0, 0, 2.65, 0, Math.PI, false);
    hoodShape.absarc(0, 0, 2.35, Math.PI, 0, true);
    add(win, new THREE.ExtrudeGeometry(hoodShape, { depth: 2.9, bevelEnabled: true, bevelThickness: 0.06, bevelSize: 0.06, bevelSegments: 2, curveSegments: 40 }),
      M.paint, [0, 0, -0.2]);
    parts.window = win;

    // siren (sağ ön)
    const siren = new THREE.Group();
    const sp = onWall(74, 11.2); siren.position.set(sp[0], sp[1], sp[2]); siren.rotation.y = 74 * D2R; body.add(siren);
    add(siren, new THREE.CylinderGeometry(2.1, 2.1, 1.8, 48), M.black, [0, 0, 0.9], [Math.PI / 2, 0, 0]);
    add(siren, new THREE.CircleGeometry(1.8, 48), new THREE.MeshStandardMaterial({ map: grilleTexture(THREE), roughness: 0.6 }), [0, 0, 1.81]);
    add(siren, new THREE.TorusGeometry(2.1, 0.12, 10, 48), M.black, [0, 0, 1.8]);
    parts.siren = siren;

    // ePTFE havalandırma (sol ön)
    const vent = new THREE.Group(); const vp = onWall(-72, 5.0); vent.position.set(vp[0], vp[1], vp[2]); vent.rotation.y = -72 * D2R; body.add(vent);
    add(vent, new THREE.CylinderGeometry(1.1, 1.1, 0.5, 6), M.black, [0, 0, 0.25], [Math.PI / 2, 0, 0]);
    add(vent, new THREE.CylinderGeometry(0.85, 0.95, 0.9, 32), M.black, [0, 0, 0.9], [Math.PI / 2, 0, 0]);
    add(vent, new THREE.CircleGeometry(0.6, 24), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1 }), [0, 0, 1.36]);
    parts.vent = vent;

    // durum LED'i ışık borusu
    const lp = onWall(-30, 12.6, 0.05);
    const statusMat = new THREE.MeshStandardMaterial({ color: 0x55ff88, emissive: 0x22ff66, emissiveIntensity: 1.2 });
    add(body, new THREE.SphereGeometry(0.22, 16, 12), statusMat, lp);
    parts.statusMat = statusMat;

    // SMA anten (sağ arka)
    const ant = new THREE.Group(); const ap = onWall(112, 14.5); ant.position.set(ap[0], ap[1], ap[2]); ant.rotation.y = 112 * D2R; body.add(ant);
    add(ant, new THREE.CylinderGeometry(0.7, 0.7, 0.45, 6), M.tin, [0, 0, 0.25], [Math.PI / 2, 0, 0]);
    add(ant, new THREE.CylinderGeometry(0.42, 0.42, 1.4, 20), M.tin, [0, 0, 1.0], [Math.PI / 2, 0, 0]);
    add(ant, new THREE.SphereGeometry(0.62, 20, 16), M.rubber, [0, 0, 1.9]);
    add(ant, new THREE.CylinderGeometry(0.42, 0.58, 19.5, 24), M.rubber, [0, 10.0, 1.9]);
    add(ant, new THREE.SphereGeometry(0.42, 16, 12), M.rubber, [0, 19.75, 1.9]);
    parts.antenna = ant;

    // PG7 kablo rakoru (arka sol)
    const gl = new THREE.Group(); const gp = onWall(-150, 15.5); gl.position.set(gp[0], gp[1], gp[2]); gl.rotation.y = -150 * D2R; body.add(gl);
    add(gl, new THREE.CylinderGeometry(0.85, 0.85, 0.5, 6), M.black, [0, 0, 0.25], [Math.PI / 2, 0, 0]);
    add(gl, new THREE.CylinderGeometry(0.6, 0.75, 1.2, 20), M.black, [0, 0, 1.0], [Math.PI / 2, 0, 0]);

    // ===== KAPAK + PANEL =====
    const lid = new THREE.Group(); lid.name = 'lid'; root.add(lid); parts.lid = lid;
    add(lid, new THREE.CylinderGeometry(R + 0.2, R + 0.2, 0.7, 128), M.paint, [0, H + 0.35, 0]);
    add(lid, new THREE.TorusGeometry(R + 0.2, 0.22, 12, 128), M.tin, [0, H + 0.7, 0], [Math.PI / 2, 0, 0]);
    add(lid, new THREE.TorusGeometry(R + 0.05, 0.12, 8, 128), M.rubber, [0, H + 0.02, 0], [Math.PI / 2, 0, 0]);
    [30, 150, 270].forEach((a) => { // kilit klipsleri
      const c = onWall(a, H - 0.2, 0.25);
      const clip = add(lid, new THREE.BoxGeometry(1.4, 2.2, 0.25), M.steel, c, [0, a * D2R, 0]);
      clip.position.y = H + 0.1;
    });
    // mapa
    add(lid, new THREE.TorusGeometry(1.0, 0.22, 14, 32), M.steel, [0, H + 2.2, -3.2]);
    add(lid, new THREE.CylinderGeometry(0.3, 0.3, 1.2, 12), M.steel, [0, H + 1.1, -3.2]);
    // panel braketi (iki yan plaka)
    const shape = new THREE.Shape();
    shape.moveTo(-6.0, 0); shape.lineTo(6.0, 0); shape.lineTo(6.0, 1.3); shape.lineTo(-6.0, 8.2); shape.lineTo(-6.0, 0);
    const hole = new THREE.Path(); hole.moveTo(-4.2, 1.1); hole.lineTo(3.4, 1.1); hole.lineTo(-4.2, 5.4); hole.lineTo(-4.2, 1.1); shape.holes.push(hole);
    const bGeo = new THREE.ExtrudeGeometry(shape, { depth: 0.3, bevelEnabled: false });
    [-6.4, 6.1].forEach((x) => {
      const b = add(lid, bGeo, M.alu, [x, H + 0.7, 0], [0, -Math.PI / 2, 0]);
      b.position.x = x + 0.3;
    });
    // panel
    const panel = new THREE.Group(); panel.position.set(0, H + 0.7 + 4.95, 0.1); panel.rotation.x = 30 * D2R; lid.add(panel);
    const pMats = [M.black, M.black, new THREE.MeshPhysicalMaterial({ map: solarTexture(THREE), roughness: 0.5, metalness: 0.0, clearcoat: 0.25, clearcoatRoughness: 0.2, envMapIntensity: 0.12, specularIntensity: 0.3 }), M.black, M.black, M.black];
    add(panel, new THREE.BoxGeometry(16.5, 0.3, 13.5), pMats);
    add(panel, new THREE.BoxGeometry(3.2, 0.7, 2.2), M.black, [0, -0.5, -4.6]); // bağlantı kutusu
    parts.panel = panel;
    // panel kablosu
    const cable = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([
      new THREE.Vector3(...onWall(-150, 15.5, 1.6)),
      new THREE.Vector3(-5.5, 17.2, -9.6),
      new THREE.Vector3(-3.0, 22.8, -8.6),
      new THREE.Vector3(-1.0, 24.6, -4.6),
    ]), 48, 0.25, 10, false), M.rubber);
    cable.castShadow = true; body.add(cable); parts.cable = cable;

    // ===== ALT: LED STROB =====
    const bottom = new THREE.Group(); bottom.name = 'bottom'; root.add(bottom); parts.bottom = bottom;
    add(bottom, new THREE.CylinderGeometry(4.0, 4.0, 0.5, 64), M.paint, [0, -0.25, 0]);
    const ring = add(bottom, new THREE.CylinderGeometry(2.6, 2.6, 0.18, 48), M.alu, [0, -0.6, 0]);
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2;
      const lm = new THREE.MeshStandardMaterial({ color: 0x5a0a06, emissive: 0xff1a0a, emissiveIntensity: 0.0, roughness: 0.3 });
      ledMats.push(lm);
      add(bottom, new THREE.CylinderGeometry(0.42, 0.42, 0.32, 20), lm, [Math.cos(a) * 1.75, -0.82, Math.sin(a) * 1.75]);
    }
    const dome = add(bottom, new THREE.SphereGeometry(3.5, 48, 24, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), M.pc, [0, -0.5, 0]);
    dome.scale.y = 0.62; dome.castShadow = false;
    const domeGlowMat = new THREE.MeshBasicMaterial({ color: 0xff2a10, transparent: true, opacity: 0.0, depthWrite: false, blending: THREE.AdditiveBlending });
    const domeGlow = add(bottom, new THREE.SphereGeometry(3.3, 32, 16, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), domeGlowMat, [0, -0.5, 0]);
    domeGlow.scale.y = 0.6; domeGlow.castShadow = false;
    parts.domeGlowMat = domeGlowMat;
    const red = new THREE.PointLight(0xff2010, 0, 260, 1.4); red.position.set(0, -3.5, 2); bottom.add(red); alarmLights.push(red);
    const red2 = new THREE.SpotLight(0xff2a14, 0, 400, 1.1, 0.6, 1.2); red2.position.set(0, -2, 0); red2.target.position.set(0, -60, 0);
    bottom.add(red2); bottom.add(red2.target); alarmLights.push(red2);

    // ===== İÇ DONANIM (patlatılmış görünümde) =====
    const interior = new THREE.Group(); interior.name = 'interior'; root.add(interior); parts.interior = interior;
    add(interior, new THREE.BoxGeometry(11.0, 15.0, 0.4), M.asa, [0, 8.5, -2.2]);
    add(interior, new THREE.CylinderGeometry(R - 0.7, R - 0.7, 0.5, 64), M.asa, [0, 0.9, 0]);
    const pcb = add(interior, new THREE.BoxGeometry(7.8, 5.8, 0.16), [M.green, M.green, M.green, M.green, new THREE.MeshStandardMaterial({ map: pcbTexture(THREE), roughness: 0.5 }), M.green], [0, 11.2, -1.6]);
    add(interior, new THREE.BoxGeometry(2.4, 2.4, 0.3), M.shield, [1.9, 11.6, -1.4]); // modem
    add(interior, new THREE.BoxGeometry(0.9, 0.9, 0.15), M.black, [-1.6, 12.0, -1.45]); // MCU
    add(interior, new THREE.BoxGeometry(0.7, 0.5, 0.15), M.black, [-1.4, 10.0, -1.45]); // CN3791
    add(interior, new THREE.BoxGeometry(1.4, 1.0, 0.25), M.rubber, [-2.6, 9.0, -1.4]); // SIM
    add(interior, new THREE.CylinderGeometry(0.55, 0.55, 0.9, 20), M.black, [2.9, 9.0, -1.0], [Math.PI / 2, 0, 0]); // kondansatör
    // batarya paketi
    const pack = new THREE.Group(); pack.position.set(0, 4.2, -0.6); interior.add(pack); parts.pack = pack;
    add(pack, new THREE.BoxGeometry(7.6, 2.0, 4.2), M.black, [0, -0.4, 0]);
    [-1.0, 1.0].forEach((z) => {
      add(pack, new THREE.CylinderGeometry(0.9, 0.9, 6.5, 32), M.cellBlue, [0, 0.55, z], [0, 0, Math.PI / 2]);
      add(pack, new THREE.CylinderGeometry(0.6, 0.6, 6.62, 20), M.tin, [0, 0.55, z], [0, 0, Math.PI / 2]);
    });
    add(interior, new THREE.BoxGeometry(2.6, 0.8, 1.8), M.silica, [3.6, 2.0, 3.0]);
    // sensör kartı (pencere arkası)
    const sns = new THREE.Group(); sns.position.set(0, 12.9, R - 1.6); sns.rotation.x = 35 * D2R; interior.add(sns); parts.sensorBoard = sns;
    add(sns, new THREE.BoxGeometry(3.0, 3.0, 0.16), M.green, [0, 0, 0]);
    add(sns, new THREE.BoxGeometry(1.2, 1.2, 0.5), M.shield, [0, 0, 0.3]);
    add(sns, new THREE.CylinderGeometry(0.35, 0.35, 0.2, 20), new THREE.MeshStandardMaterial({ color: 0x223, metalness: 0.9, roughness: 0.1 }), [0, 0, 0.62], [Math.PI / 2, 0, 0]);
    const bme = add(interior, new THREE.BoxGeometry(1.4, 1.4, 0.16), M.green, [-5.9, 5.0, 2.0], [0, -72 * D2R, 0]);
    parts.bme = bme;
    interior.visible = false;

    // ===== MONTAJ: ağaç, braket, kelepçe =====
    const mount = new THREE.Group(); mount.name = 'mount'; root.add(mount); parts.mount = mount;
    const trunkR = 13.3, trunkZ = -(R + 6.9 + trunkR);
    add(mount, new THREE.BoxGeometry(4.0, 14, 0.35), M.steel, [0, 9.5, -R - 0.15]);
    [4.0, 15.0].forEach((y) => add(mount, new THREE.BoxGeometry(3.0, 0.6, 6.4), M.steel, [0, y, -R - 3.3]));
    add(mount, new THREE.BoxGeometry(5.0, 14, 0.4), M.steel, [0, 9.5, -R - 6.5]);
    add(mount, new THREE.BoxGeometry(4.4, 13, 0.4), M.rubber, [0, 9.5, -R - 6.85]);
    const strapMat = new THREE.MeshStandardMaterial({ color: 0xd0d4d8, roughness: 0.32, metalness: 0.75 });
    parts.straps = [];
    [4.0, 15.0].forEach((y) => {
      const s = add(mount, new THREE.CylinderGeometry(trunkR + 0.95, trunkR + 0.95, 2.0, 96, 1, true), strapMat, [0, y, trunkZ]);
      s.material = strapMat.clone(); s.material.side = THREE.DoubleSide; parts.straps.push(s);
      parts.straps.push(add(mount, new THREE.BoxGeometry(2.4, 2.4, 1.4), M.steel, [(trunkR + 1.2) * Math.sin(140 * D2R), y, trunkZ + (trunkR + 1.2) * Math.cos(140 * D2R)], [0, 140 * D2R, 0]));
    });
    if (opts.tree !== false) {
      const trunkGeo = new THREE.CylinderGeometry(trunkR - 0.3, trunkR + 0.3, 220, 64, 40);
      const pos = trunkGeo.attributes.position; const r = rng(5);
      const bumps = Array.from({ length: 12 }, () => [r() * Math.PI * 2, r() * 220 - 110, 0.4 + r() * 0.9]);
      for (let i = 0; i < pos.count; i++) {
        const x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i);
        const a = Math.atan2(x, z);
        let k = 1 + 0.025 * Math.sin(a * 7 + y * 0.05) + 0.02 * Math.sin(a * 13 - y * 0.11);
        bumps.forEach(([ba, by, s]) => { const d = Math.abs(((a - ba + Math.PI * 3) % (Math.PI * 2)) - Math.PI); k += 0.04 * s * Math.exp(-(d * d) * 6 - ((y - by) ** 2) / 300); });
        pos.setX(i, x * k); pos.setZ(i, z * k);
      }
      trunkGeo.computeVertexNormals();
      const trunk = add(mount, trunkGeo, new THREE.MeshStandardMaterial({ map: barkTexture(THREE), roughness: 0.95, metalness: 0 }), [0, 40, trunkZ]);
      parts.trunk = trunk;
    }

    // ===== Etiketler (patlatılmış görünüm) =====
    const LBL = [
      [lid, [-4, 24.5, 2], [-22, 30, 2], 'L', '6V 3W güneş paneli + güneşlik'],
      [body, [8.85, 31, -3.6], [22, 40, -3.6], 'R', 'Harici LTE anten (3 dBi)'],
      [interior, [-1.6, 12.0, -1.4], [-22, 15, -1.4], 'L', 'Ana kart: ATmega328P + CN3791 MPPT'],
      [interior, [1.9, 11.6, -1.2], [22, 15, -1.2], 'R', 'LTE Cat-1 modem A7670E · SMS'],
      [interior, [-3, 4.8, 2.9], [-22, 5, 2.9], 'L', '2×18650 Li-ion · 7000 mAh'],
      [body, [0, 12.4, 9.0], [-20, 15, 2], 'L', 'AMG8833 termal kamera · HDPE pencere'],
      [body, [-8.9, 5.0, 2.9], [-20, 3, 2], 'L', 'BME680 gaz/duman · ePTFE membran'],
      [body, [9.4, 11.2, 2.7], [22, 10, 2.7], 'R', '105 dB siren'],
      [bottom, [0, -1.6, 0], [18, -3, 0], 'R', '6×1 W kırmızı LED strob'],
      [mount, [0, 9.5, -14.4], [24, 2, -14.4], 'R', 'Paslanmaz ağaç braketi + kelepçe'],
    ];
    const lineMat = new THREE.LineBasicMaterial({ color: 0x1b1f1d, transparent: true, opacity: 0.7 });
    parts.leaders = [];
    LBL.forEach(([grp, a, p, side, text]) => {
      const g = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...a), new THREE.Vector3(...p)]);
      const ln = new THREE.Line(g, lineMat); ln.visible = false; grp.add(ln); parts.leaders.push(ln);
      const anchor = new THREE.Object3D(); anchor.position.set(...p); grp.add(anchor);
      labels.push({ text, obj: anchor, offset: [0, 0, 0], side });
      const dot = new THREE.Mesh(new THREE.SphereGeometry(0.35, 12, 8), new THREE.MeshBasicMaterial({ color: 0xe4572e }));
      dot.position.set(...a); dot.visible = false; grp.add(dot); parts.leaders.push(dot);
    });

    // ===== Kontrol API =====
    const state = { explode: 0, alarm: false };
    function setExplode(t) {
      state.explode = t;
      const e = t;
      lid.position.y = 34 * e;
      bottom.position.y = -9 * e;
      interior.position.y = 20 * e;
      parts.pack.position.z = -0.6 + 3.5 * e;
      bodyFull.visible = true; bodyCut.visible = false; foam.visible = false;
      interior.visible = e > 0.02;
      cable.visible = e < 0.05;
      if (parts.trunk) parts.trunk.visible = e < 0.5;
      parts.straps.forEach((m) => { m.visible = e < 0.5 && !m.userData.hide; });
    }
    function setAlarm(on) { state.alarm = on; if (!on) applyLed(0); }
    function applyLed(v) {
      ledMats.forEach((m) => { m.emissiveIntensity = v * 6; });
      domeGlowMat.opacity = v * 0.55;
      alarmLights[0].intensity = v * 260;
      alarmLights[1].intensity = v * 1600;
    }
    function update(timeSec) {
      if (state.alarm) {
        const p = (timeSec % 1.0);
        const on = (p < 0.06) || (p > 0.15 && p < 0.21);
        applyLed(opts.still ? 1 : (on ? 1 : 0.04));
      }
      statusMat.emissiveIntensity = ((timeSec % 8) < 0.12) ? 2.5 : 0.6;
    }
    setExplode(0);
    return { root, parts, labels, setExplode, setAlarm, update, state };
  }

  // ---------- Görüntüleyici ----------
  const VIEWS = {
    hero:     { cam: [56, 28, 74], target: [-1, 17, -6], fov: 30, bg: 'day', explode: 0, alarm: false },
    front:    { cam: [0, 16, 78], target: [0, 15, 0], fov: 28, bg: 'studio', explode: 0, alarm: false, tree: false },
    side:     { cam: [-70, 22, 18], target: [0, 15, -8], fov: 30, bg: 'day', explode: 0, alarm: false },
    exploded: { cam: [64, 34, 104], target: [2, 23, 0], fov: 38, bg: 'studio', explode: 1, alarm: false, labels: true, tree: false },
    alarm:    { cam: [56, 2, 78], target: [-2, 8, -6], fov: 34, bg: 'night', explode: 0, alarm: true },
    top:      { cam: [24, 72, 40], target: [0, 18, -4], fov: 30, bg: 'day', explode: 0, alarm: false },
  };

  function ON1Viewer(THREE, A, container, opts) {
    opts = opts || {};
    const viewName = opts.view || 'hero';
    const V = Object.assign({}, VIEWS[viewName] || VIEWS.hero);
    const w = () => container.clientWidth, h = () => container.clientHeight;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(opts.pixelRatio || Math.min(window.devicePixelRatio, 2));
    renderer.setSize(w(), h());
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const pmrem = new THREE.PMREMGenerator(renderer);
    const envTex = pmrem.fromScene(new A.RoomEnvironment(), 0.04).texture;
    scene.environment = envTex;
    const moon = new THREE.DirectionalLight(0x8fa6ff, 0); moon.position.set(-40, 80, 60); scene.add(moon);

    const camera = new THREE.PerspectiveCamera(V.fov, w() / h(), 1, 2000);
    camera.position.set(...V.cam);

    const hemi = new THREE.HemisphereLight(0xe8f2ff, 0x4a5a3a, 0.8); scene.add(hemi);
    const sun = new THREE.DirectionalLight(0xfff3e0, 2.6);
    sun.position.set(60, 110, 70); sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    Object.assign(sun.shadow.camera, { left: -90, right: 90, top: 140, bottom: -90, near: 10, far: 500 });
    sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.04;
    scene.add(sun);
    const rim = new THREE.DirectionalLight(0xcfe6ff, 0.9); rim.position.set(-80, 40, -40); scene.add(rim);

    const model = buildON1(THREE, { tree: V.tree !== false && opts.tree !== false, still: !!opts.still });
    scene.add(model.root);
    if (V.tree === false) model.parts.straps.forEach((m) => { m.visible = false; m.userData.hide = true; });
    const nightBg = (function () {
      const c = document.createElement('canvas'); c.width = 64; c.height = 512; const g = c.getContext('2d');
      const gr = g.createLinearGradient(0, 0, 0, 512);
      gr.addColorStop(0, '#05070a'); gr.addColorStop(0.55, '#0b0f14'); gr.addColorStop(0.8, '#2a0f0a'); gr.addColorStop(1, '#6b2410');
      g.fillStyle = gr; g.fillRect(0, 0, 64, 512);
      const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
    })();

    // zemin gölge yakalayıcı (stüdyo)
    const shadowPlane = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.ShadowMaterial({ opacity: 0.18 }));
    shadowPlane.rotation.x = -Math.PI / 2; shadowPlane.position.y = -10; shadowPlane.receiveShadow = true; scene.add(shadowPlane);

    // gece yangın parıltısı
    const fireGlow = new THREE.PointLight(0xff7a2a, 0, 600, 1.2); fireGlow.position.set(-60, -20, -80); scene.add(fireGlow);

    let controls = null;
    if (opts.interactive) {
      controls = new A.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true; controls.dampingFactor = 0.08;
      controls.minDistance = 35; controls.maxDistance = 160;
      controls.target.set(...V.target);
      controls.autoRotate = !!opts.autoRotate; controls.autoRotateSpeed = 0.6;
    } else {
      camera.lookAt(...V.target);
    }

    // post-işlem (bloom)
    const composer = new A.EffectComposer(renderer);
    composer.addPass(new A.RenderPass(scene, camera));
    const bloom = new A.UnrealBloomPass(new THREE.Vector2(w(), h()), 0.0, 0.45, 0.8);
    composer.addPass(bloom);
    composer.addPass(new A.OutputPass());

    // etiketler
    let labelRenderer = null; const labelObjs = [];
    if (A.CSS2DRenderer) {
      labelRenderer = new A.CSS2DRenderer();
      labelRenderer.setSize(w(), h());
      Object.assign(labelRenderer.domElement.style, { position: 'absolute', inset: '0', pointerEvents: 'none' });
      container.appendChild(labelRenderer.domElement);
      model.labels.forEach((L) => {
        const el = document.createElement('div');
        el.className = 'on1-label ' + (L.side === 'L' ? 'left' : 'right');
        el.innerHTML = '<span class="in"><span class="txt"></span></span>';
        el.querySelector('.txt').textContent = L.text;
        const o = new A.CSS2DObject(el);
        o.position.set(...L.offset);
        L.obj.add(o);
        labelObjs.push(o);
      });
    }

    function applyEnv(mode) {
      container.dataset.bg = mode;
      const night = mode === 'night';
      hemi.intensity = night ? 0.06 : 0.8;
      sun.intensity = night ? 0.0 : 2.6;
      rim.intensity = night ? 0.25 : 0.9;
      rim.color.set(night ? 0x6a7cff : 0xcfe6ff);
      scene.environment = night ? null : envTex;
      scene.background = night ? nightBg : null;
      moon.intensity = night ? 0.7 : 0;
      renderer.toneMappingExposure = night ? 1.1 : 1.0;
      fireGlow.intensity = night ? 1400 : 0;
      bloom.strength = night ? 0.85 : 0.0;
      shadowPlane.visible = mode === 'studio';
    }

    const st = { explode: V.explode, explodeTarget: V.explode, alarm: V.alarm, bg: V.bg };
    model.setExplode(st.explode);
    model.setAlarm(st.alarm);
    applyEnv(st.bg);
    const showLabels = (on) => {
      labelObjs.forEach((o) => { o.visible = on; o.element.style.display = on ? '' : 'none'; });
      (model.parts.leaders || []).forEach((m) => { m.visible = on; });
    };
    showLabels(!!V.labels && opts.labels !== false);

    function resize() {
      camera.aspect = w() / h(); camera.updateProjectionMatrix();
      renderer.setSize(w(), h()); composer.setSize(w(), h());
      if (labelRenderer) labelRenderer.setSize(w(), h());
    }
    window.addEventListener('resize', resize);

    const clock = new THREE.Clock();
    let running = true;
    function frame() {
      if (!running) return;
      const t = clock.getElapsedTime();
      if (Math.abs(st.explode - st.explodeTarget) > 0.001) {
        st.explode += (st.explodeTarget - st.explode) * 0.08;
        model.setExplode(st.explode);
        showLabels(st.explode > 0.9 && st.labelsOn);
      }
      model.update(t);
      if (controls) controls.update();
      composer.render();
      if (labelRenderer) labelRenderer.render(scene, camera);
      requestAnimationFrame(frame);
    }
    st.labelsOn = !!V.labels || !!opts.labels;
    requestAnimationFrame(frame);

    return {
      renderer, scene, camera, controls, model,
      setMode(mode) { // 'assembled' | 'exploded' | 'alarm'
        st.explodeTarget = mode === 'exploded' ? 1 : 0;
        st.labelsOn = mode === 'exploded';
        if (mode !== 'exploded') showLabels(false);
        const alarm = mode === 'alarm';
        model.setAlarm(alarm);
        applyEnv(alarm ? 'night' : (mode === 'exploded' ? 'studio' : 'day'));
      },
      stop() { running = false; },
    };
  }

  window.ON1 = { buildON1, ON1Viewer, VIEWS };
})();
