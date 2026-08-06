// ===========================================================================
// clip/audio.mjs - synthesizes the bed as a 44.1 kHz stereo WAV, no dependencies.
//
// There are no recorded assets yet (AUDIO-SPEC.md describes the real mix that will
// replace this wholesale). This is four sine-and-noise layers arranged against the
// beat sheet, written straight into a PCM buffer. Doing it here rather than in an
// ffmpeg filter graph buys per-sample envelopes, which is the whole trick: the
// payoff at 18.0 s is a *hole* in the sound, and holes need sample accuracy.
//
// Levels are set by construction, not measured - the bundled ffmpeg has no
// loudnorm. See CLIP-SPEC.md 4.
// ===========================================================================
import {writeFileSync} from "node:fs";

export const RATE = 44100;

// deterministic noise, so two builds of the same clip are byte-identical
function mulberry32(a){
  return function(){
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

const clamp01 = v => v < 0 ? 0 : v > 1 ? 1 : v;
// linear ramp in, hold, ramp out
const env = (t, from, to, rise, fall) =>
  t < from || t > to ? 0 : Math.min(clamp01((t - from) / rise), clamp01((to - t) / fall));

export function render(seconds, opts){
  const o = Object.assign({
    markAt: 9.0,          // heart starts
    riserFrom: 12.4,      // it steps out of the dark
    riserTo: 15.6,        // and arrives
    dropAt: 17.95,        // you put the item down
    cardAt: 21.0
  }, opts || {});

  const n = Math.round(seconds * RATE);
  const L = new Float32Array(n), R = new Float32Array(n);
  const rnd = mulberry32(0x51AC1D);

  let brown = 0, lp1 = 0, lp2 = 0;

  for (let i = 0; i < n; i++){
    const t = i / RATE;
    let l = 0, r = 0;

    // -- room tone: brown noise through a soft lowpass. The house, breathing.
    brown = (brown + 0.018 * (rnd() * 2 - 1)) * 0.997;
    lp1 += (brown - lp1) * 0.020;
    lp2 += (lp1 - lp2) * 0.020;
    const tone = lp2 * 26;
    l += tone * 0.85; r += tone * 0.85;

    // -- drone: a fifth, detuned a hair between channels so it sits wide
    const slow = 1 + 0.10 * Math.sin(2 * Math.PI * 0.07 * t);
    l += 0.055 * slow * Math.sin(2 * Math.PI * 55.00 * t);
    r += 0.055 * slow * Math.sin(2 * Math.PI * 55.13 * t);
    l += 0.030 * Math.sin(2 * Math.PI * 82.50 * t + 1.1);
    r += 0.030 * Math.sin(2 * Math.PI * 82.62 * t + 1.1);

    // -- heart: two thumps a beat, from the mark to just after the drop
    const hb = env(t, o.markAt, o.dropAt + 1.0, 1.4, 1.2);
    if (hb > 0){
      const beat = (t - o.markAt) % 1.05;
      const thump = Math.exp(-beat * 26) + 0.55 * Math.exp(-Math.max(0, beat - 0.19) * 30);
      const s = 0.30 * hb * thump * Math.sin(2 * Math.PI * 46 * t);
      l += s; r += s;
    }

    // -- riser: swept sine, phase-integrated so the sweep is smooth, resolving on
    //    the frame it reaches the plinth. Cut dead at the drop.
    if (t >= o.riserFrom && t < o.dropAt){
      const k = clamp01((t - o.riserFrom) / (o.riserTo - o.riserFrom));
      const f0 = 150, f1 = 620;
      const dt = t - o.riserFrom;
      const phase = 2 * Math.PI * (f0 * dt + (f1 - f0) * dt * dt / (2 * (o.riserTo - o.riserFrom)));
      const amp = 0.085 * Math.pow(k, 1.6) * (t > o.riserTo ? Math.exp(-(t - o.riserTo) * 1.1) : 1);
      l += amp * Math.sin(phase);
      r += amp * Math.sin(phase * 1.001 + 0.4);
    }

    // -- the payoff is silence: everything ducks hard for 260 ms at the drop
    if (t >= o.dropAt && t < o.dropAt + 0.60){
      const d = t - o.dropAt;
      const duck = d < 0.26 ? 0.10 : 0.10 + 0.90 * clamp01((d - 0.26) / 0.34);
      l *= duck; r *= duck;
    }

    // -- title card: let the drone breathe out
    if (t >= o.cardAt){
      const k = clamp01((t - o.cardAt) / 1.2);
      const g = 1 - 0.35 * k;
      l *= g; r *= g;
    }

    // -- top and tail
    const io = Math.min(clamp01(t / 0.30), clamp01((seconds - t) / 0.55));
    L[i] = l * io; R[i] = r * io;
  }

  return {L, R, rate: RATE, frames: n};
}

export function toWav({L, R, rate, frames}){
  const bytes = frames * 4;                       // 16-bit stereo
  const buf = Buffer.alloc(44 + bytes);
  buf.write("RIFF", 0); buf.writeUInt32LE(36 + bytes, 4); buf.write("WAVE", 8);
  buf.write("fmt ", 12); buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20);
  buf.writeUInt16LE(2, 22); buf.writeUInt32LE(rate, 24);
  buf.writeUInt32LE(rate * 4, 28); buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34);
  buf.write("data", 36); buf.writeUInt32LE(bytes, 40);
  let peak = 0;
  for (let i = 0; i < frames; i++) peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
  const g = peak > 0.89 ? 0.89 / peak : 1;        // headroom, never a limiter
  for (let i = 0; i < frames; i++){
    buf.writeInt16LE(Math.round(Math.max(-1, Math.min(1, L[i] * g)) * 32767), 44 + i * 4);
    buf.writeInt16LE(Math.round(Math.max(-1, Math.min(1, R[i] * g)) * 32767), 46 + i * 4);
  }
  return buf;
}

export function write(path, seconds, opts){
  const buf = toWav(render(seconds, opts));
  writeFileSync(path, buf);
  return buf.length;
}

if (import.meta.url === `file://${process.argv[1]}`){
  const out = process.argv[2] || "clip/build/bed.wav";
  const secs = Number(process.argv[3] || 24);
  console.log(`  bed  ${write(out, secs)} bytes  ${secs}s -> ${out}`);
}
