// ===========================================================================
// clip/audio.mjs - synthesizes the bed as a 44.1 kHz stereo WAV, no dependencies.
//
// There are no recorded assets yet (AUDIO-SPEC.md describes the real mix that will
// replace this wholesale). This is four sine-and-noise layers arranged against the
// beat sheet, written straight into a PCM buffer. Doing it here rather than in an
// ffmpeg filter graph buys per-sample envelopes, which is the whole trick: the
// payoff at 18.0 s is a *hole* in the sound, and holes need sample accuracy.
//
// Levels are MEASURED, not guessed - see CLIP-SPEC.md 4 and 5 (gate G11). The bundled
// ffmpeg has no loudnorm, so the yardstick is a phone-speaker model: 48 dB/oct below
// 500 Hz, gentle top at 8 kHz. What survives that filter is what a viewer hears.
// ===========================================================================
import {writeFileSync} from "node:fs";

export const RATE = 44100;

// Master trim. Unity, because the layer gains below already land the mix at -2.2 dBFS
// peak / -22.7 dBFS RMS. If you change a layer, re-run `node clip/check.mjs`: G11
// measures what a phone speaker can reproduce and fails if the bed drifts back down
// into the sub-bass it started in.
const MASTER = 1.0;

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

  let brown = 0, lp1 = 0, lp2 = 0, air = 0, tk1 = 0, tk2 = 0;

  for (let i = 0; i < n; i++){
    const t = i / RATE;
    let l = 0, r = 0;

    // -- room tone: brown noise through a soft lowpass. The house, breathing.
    brown = (brown + 0.018 * (rnd() * 2 - 1)) * 0.997;
    lp1 += (brown - lp1) * 0.020;
    lp2 += (lp1 - lp2) * 0.020;
    // Gain 26 here was a guess, and it was 100x too hot: the layer measured +10 dBFS
    // RMS and peaked at 11.9, so toWav's safety normalizer pulled the WHOLE mix down
    // 22.5 dB and every other layer with it. 0.20 puts it at -32 dBFS, which is what
    // CLIP-SPEC 4 always said it was. See CLIP_LOG C9.
    const tone = lp2 * 0.20;
    l += tone * 0.85; r += tone * 0.85;

    // -- air: the same noise with the bottom taken out. Inaudible on headphones,
    //    and on a phone speaker it is most of what the room tone becomes.
    const wh = rnd() * 2 - 1;
    air += (wh - air) * 0.155;                  // ~1.1 kHz one-pole
    const hiss = (wh - air) * 0.085 * (1 + 0.35 * Math.sin(2 * Math.PI * 0.11 * t));
    l += hiss; r += hiss * 0.92;

    // -- drone: a fifth, detuned a hair between channels so it sits wide.
    //    The 55/82.5 Hz fundamentals carry it on headphones; the partials at 220,
    //    330 and 440 are what a phone speaker actually reproduces (see C9 - the
    //    first version of this bed put 99% of its energy below 450 Hz).
    const slow = 1 + 0.10 * Math.sin(2 * Math.PI * 0.07 * t);
    l += 0.055 * slow * Math.sin(2 * Math.PI * 55.00 * t);
    r += 0.055 * slow * Math.sin(2 * Math.PI * 55.13 * t);
    l += 0.030 * Math.sin(2 * Math.PI * 82.50 * t + 1.1);
    r += 0.030 * Math.sin(2 * Math.PI * 82.62 * t + 1.1);
    const part = 1 + 0.22 * Math.sin(2 * Math.PI * 0.052 * t + 2.0);
    l += 0.0165 * part * Math.sin(2 * Math.PI * 220.0 * t + 0.7);
    r += 0.0165 * part * Math.sin(2 * Math.PI * 220.4 * t + 0.7);
    l += 0.0105 * part * Math.sin(2 * Math.PI * 330.0 * t + 2.3);
    r += 0.0105 * part * Math.sin(2 * Math.PI * 330.6 * t + 2.3);
    l += 0.0140 * part * Math.sin(2 * Math.PI * 440.0 * t + 1.4);
    r += 0.0140 * part * Math.sin(2 * Math.PI * 441.1 * t + 1.4);
    l += 0.0095 * Math.sin(2 * Math.PI * 660.0 * t + 0.2);
    r += 0.0095 * Math.sin(2 * Math.PI * 661.3 * t + 0.2);
    l += 0.0055 * Math.sin(2 * Math.PI * 880.0 * t + 2.8);
    r += 0.0055 * Math.sin(2 * Math.PI * 881.7 * t + 2.8);

    // -- heart: two thumps a beat, from the mark to just after the drop
    const hb = env(t, o.markAt, o.dropAt + 1.0, 1.4, 1.2);
    if (hb > 0){
      const beat = (t - o.markAt) % 1.05;
      const thump = Math.exp(-beat * 26) + 0.55 * Math.exp(-Math.max(0, beat - 0.19) * 30);
      const s = 0.30 * hb * thump * Math.sin(2 * Math.PI * 46 * t);
      l += s; r += s;
      // Each thump also gets a band-limited knock around 700-1400 Hz. A 46 Hz pulse
      // is felt, not heard, and on a phone it is not even felt - the knock is the
      // part that survives.
      tk1 += (wh - tk1) * 0.175;                // ~1.3 kHz
      tk2 += (wh - tk2) * 0.055;                // ~390 Hz
      const knock = (tk1 - tk2) * 0.75 * hb *
                    (Math.exp(-beat * 42) + 0.5 * Math.exp(-Math.max(0, beat - 0.19) * 48));
      l += knock; r += knock * 0.96;
    }

    // -- riser: swept sine, phase-integrated so the sweep is smooth, resolving on
    //    the frame it reaches the plinth. Cut dead at the drop.
    if (t >= o.riserFrom && t < o.dropAt){
      const k = clamp01((t - o.riserFrom) / (o.riserTo - o.riserFrom));
      const f0 = 210, f1 = 1150;                // was 150->620, half of it inaudible
      const dt = t - o.riserFrom;
      const phase = 2 * Math.PI * (f0 * dt + (f1 - f0) * dt * dt / (2 * (o.riserTo - o.riserFrom)));
      const amp = 0.085 * Math.pow(k, 1.6) * (t > o.riserTo ? Math.exp(-(t - o.riserTo) * 1.1) : 1);
      l += amp * Math.sin(phase);
      r += amp * Math.sin(phase * 1.001 + 0.4);
      l += amp * 0.30 * Math.sin(phase * 1.5 + 0.9);   // a fifth above, to give it edge
      r += amp * 0.30 * Math.sin(phase * 1.502 + 0.9);
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

    // -- top and tail, then a fixed master gain. Fixed, not normalised: peak
    //    normalisation is what let one bad layer gain silently rewrite the mix.
    const io = Math.min(clamp01(t / 0.30), clamp01((seconds - t) / 0.55));
    L[i] = l * io * MASTER; R[i] = r * io * MASTER;
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
  // A guard against clipping, NOT the mix's level control. It used to trigger on
  // every build at 0.89 and quietly scale the whole bed by -22 dB, which is how one
  // wrong layer gain (C9) stayed invisible for eight rounds. MASTER sets the level;
  // if this ever fires, a layer is wrong - fix the layer.
  const g = peak > 0.98 ? 0.98 / peak : 1;
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
