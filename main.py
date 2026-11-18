<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FF CLONE — Battle Royale</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#0a0a0c;overflow:hidden;font-family:'Segoe UI',system-ui,sans-serif;color:#f3f3f6}
  canvas{display:block}
  #hud{position:fixed;inset:0;pointer-events:none;padding:18px}
  .bar{width:240px;height:14px;background:#000;border:1px solid #333;overflow:hidden}
  .bar i{display:block;height:100%;background:linear-gradient(90deg,#ff6a00,#ffa500);transition:width .12s}
  #hpRow{display:flex;align-items:center;gap:10px;margin-bottom:8px}
  #hpTxt{font-size:12px;font-weight:800;letter-spacing:1px}
  #top{display:flex;gap:22px;font-size:12px;letter-spacing:2px;text-transform:uppercase}
  #top b{color:#ffa500;font-size:16px}
  #zoneTxt{position:fixed;top:18px;left:50%;transform:translateX(-50%);font-size:12px;letter-spacing:3px;text-transform:uppercase;color:#ffa500}
  #msg{position:fixed;inset:0;display:grid;place-items:center;background:rgba(5,5,8,.88);text-align:center;padding:24px}
  #msg.hidden{display:none}
  #msg h1{font-size:34px;letter-spacing:6px;text-transform:uppercase;margin-bottom:10px}
  #msg p{color:#8b8b96;font-size:13px;line-height:1.9;margin-bottom:22px}
  #msg kbd{background:#1a1a20;border:1px solid #333;padding:2px 7px;font-family:inherit;font-size:12px}
  #msg button{background:linear-gradient(140deg,#ff6a00,#ffa500);color:#0a0a0c;border:none;font-weight:900;letter-spacing:2px;text-transform:uppercase;padding:14px 34px;cursor:pointer;clip-path:polygon(10% 0,100% 0,90% 100%,0 100%)}
  #msg button:hover{filter:brightness(1.15)}
</style>
</head>
<body>
<canvas id="c"></canvas>
<div id="hud">
  <div id="hpRow"><div class="bar"><i id="hpBar" style="width:100%"></i></div><span id="hpTxt">100</span></div>
  <div id="top"><span>Kills <b id="kills">0</b></span><span>Vivos <b id="alive">0</b></span><span>Balas <b id="ammo">∞</b></span></div>
</div>
<div id="zoneTxt">La zona se cierra</div>
<div id="msg">
  <div>
    <h1 id="mTitle">FF CLONE</h1>
    <p id="mText"><kbd>WASD</kbd> mover · <kbd>Ratón</kbd> apuntar · <kbd>Clic</kbd> disparar<br>Sobrevive a los bots y a la zona que se cierra.</p>
    <button id="start">Empezar</button>
  </div>
</div>
<script>
(() => {
  const cv = document.getElementById('c'), ctx = cv.getContext('2d');
  let W, H;
  const resize = () => { W = cv.width = innerWidth; H = cv.height = innerHeight; };
  addEventListener('resize', resize); resize();

  const keys = {};
  const mouse = { x: 0, y: 0 };
  let running = false, t = 0, last = 0;

  const P = { x: 0, y: 0, r: 14, hp: 100, kills: 0, cool: 0, speed: 210 };
  let bots = [], bullets = [], meds = [], zone = null;

  const rand = (a, b) => a + Math.random() * (b - a);
  const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);

  addEventListener('keydown', e => { keys[e.key.toLowerCase()] = true; });
  addEventListener('keyup', e => { keys[e.key.toLowerCase()] = false; });
  addEventListener('mousemove', e => { mouse.x = e.clientX; mouse.y = e.clientY; });
  addEventListener('mousedown', () => { if (running) shoot(); });

  function shoot() {
    if (P.cool > 0) return;
    P.cool = 0.11;
    const a = Math.atan2(mouse.y - P.y, mouse.x - P.x);
    bullets.push({ x: P.x, y: P.y, vx: Math.cos(a) * 760, vy: Math.sin(a) * 760, life: 1.3, own: 'p' });
  }

  function spawnBot() {
    const a = rand(0, Math.PI * 2), d = rand(380, 640);
    bots.push({
      x: W / 2 + Math.cos(a) * d, y: H / 2 + Math.sin(a) * d,
      r: 13, hp: 100, cool: rand(0.4, 1.4), speed: rand(78, 118),
      drift: rand(0, 6.28), acc: 0.6 + Math.random() * 0.5
    });
  }

  function reset() {
    P.x = W / 2; P.y = H / 2; P.hp = 100; P.kills = 0; P.cool = 0;
    bots = []; bullets = []; meds = [];
    zone = { x: W / 2, y: H / 2, r: Math.max(W, H) * 0.62, tr: 130, timer: 26 };
    for (let i = 0; i < 8; i++) spawnBot();
    for (let i = 0; i < 5; i++) meds.push({ x: rand(80, W - 80), y: rand(80, H - 80), r: 10, t: 0 });
    t = 0;
  }

  function hud() {
    document.getElementById('hpBar').style.width = Math.max(0, P.hp) + '%';
    document.getElementById('hpTxt').textContent = Math.max(0, Math.round(P.hp));
    document.getElementById('kills').textContent = P.kills;
    document.getElementById('alive').textContent = bots.length + 1;
    document.getElementById('zoneTxt').textContent = zone.timer > 0
      ? 'La zona se cierra en ' + Math.ceil(zone.timer) + 's'
      : '¡Fuera de la zona!';
  }

  function over(win) {
    running = false;
    const m = document.getElementById('msg');
    m.classList.remove('hidden');
    document.getElementById('mTitle').textContent = win ? 'BOOYAH' : 'ELIMINADO';
    document.getElementById('mText').innerHTML = win
      ? 'Ganaste la partida con <b>' + P.kills + '</b> bajas.'
      : 'Quedaste con <b>' + P.kills + '</b> bajas.';
    document.getElementById('start').textContent = 'Reintentar';
  }

  function update(dt) {
    t += dt;
    P.cool -= dt;

    // movimiento jugador
    let dx = 0, dy = 0;
    if (keys['w'] || keys['arrowup']) dy--;
    if (keys['s'] || keys['arrowdown']) dy++;
    if (keys['a'] || keys['arrowleft']) dx--;
    if (keys['d'] || keys['arrowright']) dx++;
    const len = Math.hypot(dx, dy) || 1;
    P.x += (dx / len) * P.speed * dt;
    P.y += (dy / len) * P.speed * dt;
    P.x = Math.max(P.r, Math.min(W - P.r, P.x));
    P.y = Math.max(P.r, Math.min(H - P.r, P.y));

    // zona
    if (zone.timer > 0) zone.timer -= dt;
    else {
      zone.r += (zone.tr - zone.r) * Math.min(1, dt * 0.35);
      if (zone.timer < -14) { zone.timer = 26; zone.tr = Math.max(70, zone.tr * 0.72); }
    }
    if (dist(P, zone) > zone.r) P.hp -= 9 * dt;

    // bots
    for (const b of bots) {
      const d = dist(b, P);
      b.cool -= dt;
      if (d < 460) {
        const a = Math.atan2(P.y - b.y, P.x - b.x);
        b.x += Math.cos(a) * b.speed * dt;
        b.y += Math.sin(a) * b.speed * dt;
        if (b.cool <= 0) {
          b.cool = rand(0.45, 0.95);
          const jit = rand(-0.16, 0.16);
          bullets.push({
            x: b.x, y: b.y, vx: Math.cos(a + jit) * 520, vy: Math.sin(a + jit) * 520,
            life: 1.4, own: 'b', dmg: 8 * b.acc
          });
        }
      } else {
        b.drift += rand(-0.4, 0.4);
        b.x += Math.cos(b.drift) * b.speed * 0.5 * dt;
        b.y += Math.sin(b.drift) * b.speed * 0.5 * dt;
      }
      b.x = Math.max(b.r, Math.min(W - b.r, b.x));
      b.y = Math.max(b.r, Math.min(H - b.r, b.y));
      if (dist(b, zone) > zone.r) b.hp -= 9 * dt;
    }

    // balas
    for (const bl of bullets) {
      bl.x += bl.vx * dt; bl.y += bl.vy * dt; bl.life -= dt;
      if (bl.own === 'p') {
        for (const b of bots) {
          if (dist(bl, b) < b.r + 3) { b.hp -= 24; bl.life = 0; break; }
        }
      } else if (dist(bl, P) < P.r + 3) {
        P.hp -= bl.dmg; bl.life = 0;
      }
      if (bl.x < 0 || bl.y < 0 || bl.x > W || bl.y > H) bl.life = 0;
    }
    bullets = bullets.filter(b => b.life > 0);

    // bajas
    const before = bots.length;
    bots = bots.filter(b => {
      if (b.hp > 0) return true;
      P.kills++;
      if (Math.random() < 0.55) meds.push({ x: b.x, y: b.y, r: 10, t: 0 });
      return false;
    });
    if (bots.length < before && bots.length > 0 && t > 3) spawnBot();

    // botiquines
    for (const m of meds) {
      m.t += dt;
      if (dist(m, P) < P.r + m.r && P.hp < 100) {
        P.hp = Math.min(100, P.hp + 28);
        m.t = 99;
      }
    }
    meds = meds.filter(m => m.t < 99);

    if (P.hp <= 0) return over(false);
    if (!bots.length) return over(true);
  }

  function draw() {
    ctx.fillStyle = '#0d0f12';
    ctx.fillRect(0, 0, W, H);

    // rejilla
    ctx.strokeStyle = 'rgba(255,106,0,.05)';
    ctx.lineWidth = 1;
    for (let x = 0; x < W; x += 64) { ctx.beginPath(); ctx.moveTo(x,