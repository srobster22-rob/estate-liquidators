// ===========================================================================
// clip/director.js - injected into proto3d/index.html BEFORE its own script runs.
//
// Three jobs, all of them about making a real-time game recordable frame by frame:
//
//   1. Determinism. Seeded Math.random, so the estate rolls identically every build.
//   2. A virtual clock. requestAnimationFrame is trapped and pumped by hand, so the
//      sim advances exactly 1/30 s per captured frame no matter how slow the headless
//      renderer actually is. A dropped frame changes the film, not the timing.
//   3. The overlay. Captions and the title card live in the DOM on top of the canvas,
//      so they land in the page screenshot without a compositing pass.
//
// Nothing here touches a game rule. Staging goes through window.__d (proto3d) and the
// performance itself is data in clip/shots.js.
// ===========================================================================
(() => {
"use strict";

// ------------------------------------------------------------------ determinism
function mulberry32(a){
  return function(){
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
const SEED = Number(new URLSearchParams(location.search).get("seed") || 20260806);
Math.random = mulberry32(SEED);

// ------------------------------------------------------------------ virtual clock
let pending = null, vnow = 0;
const realNow = performance.now.bind(performance);
window.requestAnimationFrame = cb => { pending = cb; return 1; };
window.cancelAnimationFrame = () => { pending = null; };
performance.now = () => vnow;
Date.now = () => 1767225600000 + vnow;   // fixed wall clock; nothing should read it

// WebGL screenshots come back blank if the drawing buffer is swapped before the
// capture lands. Force preservation for every context the page asks for.
const getContext = HTMLCanvasElement.prototype.getContext;
HTMLCanvasElement.prototype.getContext = function(type, attrs){
  if (type === "webgl" || type === "webgl2" || type === "experimental-webgl")
    attrs = Object.assign({}, attrs, {preserveDrawingBuffer: true});
  return getContext.call(this, type, attrs);
};

// ------------------------------------------------------------------ overlay
const CSS = `
/* The prototype's HUD is sized for a 1080p desktop window. At 1080x1920 on a phone
   it is unreadable, and the HUD is half the story here - the carried value, the
   Disturbance tier, and IT IS COMING FOR YOU all have to land. Scale it up and pull
   it out of the platform's top overlay strip. Presentation only; no text changes. */
#hud{transform:scale(2.45)!important;transform-origin:0 0!important;
  left:64px!important;top:206px!important}
#prompt{transform:translateX(-50%) scale(2.15)!important;top:calc(50% + 58px)!important}
#cross{width:9px!important;height:9px!important;margin:-4.5px 0 0 -4.5px!important;
  opacity:.42!important}

#clip-ov{position:fixed;inset:0;pointer-events:none;font-family:ui-monospace,"SF Mono",
  Menlo,Consolas,monospace;z-index:50}
#clip-ov .cap{position:absolute;left:64px;width:836px;color:#efeade;font-size:52px;
  line-height:1.28;letter-spacing:.005em;font-weight:500;opacity:0;
  text-shadow:0 3px 22px rgba(0,0,0,.95),0 1px 3px rgba(0,0,0,1)}
#clip-ov .cap .lo{color:#a8a49a}
#clip-ov .cap .hi{color:#9fc4d6}
#clip-ov #vig{position:absolute;inset:0;opacity:0;
  background:radial-gradient(120% 78% at 50% 46%,rgba(0,0,0,0) 42%,rgba(0,0,0,.72) 100%)}
#clip-ov #card{position:absolute;left:64px;width:836px;top:760px;opacity:0;text-align:center}
#clip-ov #card h1{font-family:Georgia,"Times New Roman",serif;font-weight:400;
  font-size:86px;letter-spacing:.10em;margin:0 0 26px;color:#efeade;
  text-shadow:0 4px 30px rgba(0,0,0,.95)}
#clip-ov #card p{margin:0;font-size:34px;letter-spacing:.16em;color:#a8a49a;
  text-shadow:0 2px 12px rgba(0,0,0,.95)}
#clip-ov #fade{position:absolute;inset:0;background:#06070a;opacity:0}
`;

const ov = {el:null, cap:null, card:null, vig:null, fade:null};
function buildOverlay(){
  if (ov.el) return;
  const style = document.createElement("style");
  style.textContent = CSS;
  document.head.appendChild(style);
  const root = document.createElement("div");
  root.id = "clip-ov";
  root.innerHTML =
    `<div id="vig"></div>` +
    `<div class="cap" id="cap"></div>` +
    `<div id="card"><h1>ESTATE LIQUIDATORS</h1>` +
    `<p>CO-OP HORROR EXTRACTION</p></div>` +
    `<div id="fade"></div>`;
  document.body.appendChild(root);
  ov.el = root;
  ov.cap = root.querySelector("#cap");
  ov.card = root.querySelector("#card");
  ov.vig = root.querySelector("#vig");
  ov.fade = root.querySelector("#fade");
}

// ------------------------------------------------------------------ camera helpers
const TAU = Math.PI * 2;
function angLerp(a, b, k){
  let d = (b - a) % TAU;
  if (d > Math.PI) d -= TAU; else if (d < -Math.PI) d += TAU;
  return a + d * k;
}
const lerp  = (a, b, k) => a + (b - a) * k;
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
// smoothstep-based easing; ease(0)=0, ease(1)=1, zero velocity at both ends
const ease  = k => { k = clamp(k, 0, 1); return k * k * (3 - 2 * k); };

const cam = {
  yaw: 0, pitch: 0,          // smoothed camera state, authoritative
  tYaw: 0, tPitch: 0,        // where the shot wants it
  k: 0.10,                   // smoothing per frame at 30fps
  bob: 1.0                   // handheld amplitude multiplier
};
const pos = {x: 0, z: 0, tx: 0, tz: 0, k: 0.14};

function lookAt(x, z, y){
  const p = window.__d.player();
  const dx = x - p.x, dz = z - p.z;
  cam.tYaw = Math.atan2(dx, dz);
  cam.tPitch = Math.atan2((y === undefined ? window.__d.eyeHeight() : y) - window.__d.eyeHeight(),
                          Math.max(0.25, Math.hypot(dx, dz)));
}
function lookYaw(yaw, pitch){ cam.tYaw = yaw; cam.tPitch = pitch === undefined ? 0 : pitch; }

// Put a world point at a chosen height in frame instead of dead centre.
// `up` is a fraction of the half-frame: 0 centres it, +1 is the top edge.
//
// This exists because a carried item is view-locked - proto3d hangs it 1.15 m down
// the look ray, 0.30 m below it - so it always occupies the bottom of frame no
// matter where you aim. Centring the Curator therefore hides it behind your own
// loot. Framing it high puts the world above the cargo, which is also the honest
// composition: the thing you stole in the bottom third, the thing coming for it
// above.  HALF_FOV mirrors proto3d's M4.persp(1.15, ...).
const HALF_FOV = 1.15 / 2;
function frameAt(x, z, worldY, up){
  const p = window.__d.player();
  const eye = window.__d.eyeHeight();
  const dist = Math.max(0.25, Math.hypot(x - p.x, z - p.z));
  cam.tYaw = Math.atan2(x - p.x, z - p.z);
  cam.tPitch = Math.atan2((worldY === undefined ? eye : worldY) - eye, dist)
             - Math.atan((up || 0) * Math.tan(HALF_FOV));
}
function moveTo(x, z){ pos.tx = x; pos.tz = z; }
function snapTo(x, z, yaw, pitch){
  pos.x = pos.tx = x; pos.z = pos.tz = z;
  cam.yaw = cam.tYaw = yaw; cam.pitch = cam.tPitch = pitch || 0;
  window.__d.pose(x, z, yaw, pitch || 0);
}

// ------------------------------------------------------------------ runtime
const clip = {
  fps: 30,
  frame: 0,
  seed: SEED,
  trace: [],
  captionSpans: [],           // [{from,to,text}] recorded for the safe-area gate
  _capText: null,
  _capFrom: 0,

  // -- shot API used by clip/shots.js -------------------------------------
  lookAt, lookYaw, frameAt, moveTo, snapTo, cam, pos, lerp, angLerp, ease, clamp,
  d: () => window.__d,
  g: () => window.__g,

  caption(html, opts){
    buildOverlay();
    const o = opts || {};
    if (html === null){
      if (this._capText !== null){
        this.captionSpans.push({from: this._capFrom, to: this.frame, text: this._capText});
        this._capText = null;
      }
      ov.cap.style.opacity = "0";
      return;
    }
    if (html !== this._capText){
      if (this._capText !== null)
        this.captionSpans.push({from: this._capFrom, to: this.frame, text: this._capText});
      this._capText = html;
      this._capFrom = this.frame;
      ov.cap.innerHTML = html;
    }
    ov.cap.style.top = (o.top === undefined ? 1180 : o.top) + "px";
    ov.cap.style.opacity = String(o.alpha === undefined ? 1 : o.alpha);
  },
  // The game's own HUD and interaction prompt. They carry half the story while the
  // clip is running, and clutter the title card once it is over.
  chrome(hud, prompt){
    const h = document.getElementById("hud"), p = document.getElementById("prompt");
    if (h) h.style.opacity = String(hud);
    if (p) p.style.opacity = String(prompt === undefined ? hud : prompt);
  },
  vignette(a){ buildOverlay(); ov.vig.style.opacity = String(a); },
  card(a){ buildOverlay(); ov.card.style.opacity = String(a); },
  fade(a){ buildOverlay(); ov.fade.style.opacity = String(a); },

  // -- per-frame drive ----------------------------------------------------
  // Applies the shot script for frame n, pumps exactly one simulated frame, and
  // records the state trace the rules-true gate (G9) reads afterwards.
  step(n){
    this.frame = n;
    const t = n / this.fps;
    const S = window.__shots;

    S.update(t, this);

    // camera + dolly smoothing, then handheld bob, then commit the pose
    cam.yaw   = angLerp(cam.yaw, cam.tYaw, cam.k);
    cam.pitch = lerp(cam.pitch, cam.tPitch, cam.k);
    pos.x = lerp(pos.x, pos.tx, pos.k);
    pos.z = lerp(pos.z, pos.tz, pos.k);
    const bobY = Math.sin(t * 2.30) * 0.0075 + Math.sin(t * 0.87) * 0.0060;
    const bobP = Math.sin(t * 1.70) * 0.0060 + Math.sin(t * 3.10) * 0.0028;
    window.__d.pose(pos.x, pos.z, cam.yaw + bobY * cam.bob, cam.pitch + bobP * cam.bob);

    // advance one frame of the real game loop
    vnow += 1000 / this.fps;
    const cb = pending; pending = null;
    if (cb) cb(vnow);

    const st = window.__g.state(), cu = window.__d.curator(), pl = window.__d.player();
    const capAlpha = ov.cap ? +ov.cap.style.opacity : 0;
    const cardAlpha = ov.card ? +ov.card.style.opacity : 0;
    let box = null;
    if (capAlpha > 0.02 || cardAlpha > 0.02){
      const el = capAlpha > 0.02 ? ov.cap : ov.card;
      const r = el.getBoundingClientRect();
      box = [Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)];
    }
    this.trace.push({n, t: +t.toFixed(3), dist: st.dist, tier: st.tier, cur: cu.state,
      marked: st.marked, holding: st.holding, goal: cu.goal,
      px: +pl.x.toFixed(2), pz: +pl.z.toFixed(2),
      cx: +cu.x.toFixed(2), cz: +cu.z.toFixed(2),
      caption: this._capText, capAlpha, cardAlpha, box});
    return true;
  },

  boot(){
    buildOverlay();
    const start = document.getElementById("start");
    if (start) start.style.display = "none";
    const end = document.getElementById("end");
    if (end) end.style.display = "none";
    window.__d.begin();
    window.__shots.setup(this);
    // one pump so the first captured frame is already rendered
    const cb = pending; pending = null; if (cb) cb(vnow);
  }
};

window.__clip = clip;
window.__realNow = realNow;
})();
