// ===========================================================================
// clip/check.mjs - the done gates from CLIP-SPEC.md 5.
//
// Every gate reads the *built artefact* or the state trace the capture recorded,
// never the shot script's intentions. G9 is the one with teeth: it asserts the clip
// is telling the truth about the game's rules, so a tuning change that breaks the
// claim breaks the build instead of quietly shipping a lie.
//
//   node clip/check.mjs [--in clip/build] [--file <mp4>]
// ===========================================================================
import {execFileSync} from "node:child_process";
import {existsSync, readFileSync, statSync} from "node:fs";
import {dirname, join, resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {findFfmpeg} from "./encode.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf("--" + n); return i >= 0 ? argv[i + 1] : d; };

const SPEC = {
  width: 1080, height: 1920, fps: 30,
  seconds: 24.0, secondsTol: 0.2, avSkew: 0.15,
  maxBytes: 12e6,
  safe: {x0: 64, y0: 200, x1: 900, y1: 1480},
  darkFrac: 0.97, darkLuma: 10,
  openDark: 12,          // frames of the opening fade that may be black
  tailFrom: 630,         // 21.0s: title card may hold still
  phoneRms: -40,         // dBFS through the phone-speaker model, minimum
  peakMax: -0.5          // dBFS true peak, maximum
};

// A phone speaker, roughly: nothing below 500 Hz (48 dB/oct), gentle top at 8 kHz.
// Validated against tones - unity at 1 kHz, -12 dB at 500 Hz, -58 dB at 200 Hz.
// The bed's whole reason to exist is what comes through this.
const PHONE = ["highpass=f=500:poles=2", "highpass=f=500:poles=2",
               "highpass=f=500:poles=2", "highpass=f=500:poles=2",
               "lowpass=f=8000"].join(",");

const results = [];
const gate = (id, name, ok, detail) => results.push({id, name, ok: !!ok, detail});

function probe(ffmpeg, file){
  let err = "";
  try { execFileSync(ffmpeg, ["-hide_banner", "-i", file], {encoding: "utf8", stdio: ["ignore", "pipe", "pipe"]}); }
  catch (e) { err = String(e.stderr || ""); }
  const v = err.match(/Stream #\d+:\d+.*?: Video: ([a-z0-9]+)[^\n]*/i);
  const a = err.match(/Stream #\d+:\d+.*?: Audio: ([a-z0-9]+)[^\n]*/i);
  const dur = err.match(/Duration: (\d+):(\d+):([\d.]+)/);
  const geom = v && v[0].match(/, (\d{2,5})x(\d{2,5})[ ,]/);
  const fps = v && v[0].match(/([\d.]+) fps/);
  return {
    raw: err,
    vcodec: v && v[1], acodec: a && a[1],
    pixfmt: v && (v[0].match(/(yuv[0-9a-z]+)/) || [])[1],
    profile: v && (v[0].match(/Video: h264 \(([^)]+)\)/) || [])[1],
    width: geom && +geom[1], height: geom && +geom[2],
    fps: fps && +fps[1],
    duration: dur ? +dur[1] * 3600 + +dur[2] * 60 + +dur[3] : null,
    audioRate: a && +((a[0].match(/(\d+) Hz/) || [])[1]),
    channels: a && /stereo/.test(a[0]) ? 2 : a ? 1 : 0
  };
}

// Decode the finished video to a tiny greyscale so darkness and freezes can be
// measured on what a viewer actually sees - after the grade, not before it.
function lumaFrames(ffmpeg, file, w = 24, h = 42){
  const buf = execFileSync(ffmpeg,
    ["-hide_banner", "-loglevel", "error", "-i", file, "-map", "0:v",
     "-vf", `scale=${w}:${h}`, "-pix_fmt", "gray", "-f", "rawvideo", "-"],
    {maxBuffer: 1 << 28, encoding: "buffer"});
  const size = w * h, out = [];
  for (let i = 0; i + size <= buf.length; i += size) out.push(buf.subarray(i, i + size));
  return out;
}

function audioRms(ffmpeg, file, filter){
  const buf = execFileSync(ffmpeg,
    ["-hide_banner", "-loglevel", "error", "-i", file, "-map", "0:a",
     ...(filter ? ["-af", filter] : []),
     "-f", "s16le", "-acodec", "pcm_s16le", "-ac", "2", "-ar", "44100", "-"],
    {maxBuffer: 1 << 28, encoding: "buffer"});
  const n = Math.floor(buf.length / 4);
  let sum = 0, peak = 0;
  for (let i = 0; i < n; i++){
    const s = buf.readInt16LE(i * 4) / 32768;
    sum += s * s; peak = Math.max(peak, Math.abs(s));
  }
  return {seconds: n / 44100, rms: Math.sqrt(sum / Math.max(n, 1)), peak};
}

const dbfs = v => 20 * Math.log10(Math.max(v, 1e-9));

function main(){
  const inDir = resolve(ROOT, arg("in", "clip/build"));
  const file = resolve(ROOT, arg("file", "clip/estate-liquidators.mp4"));
  if (!existsSync(file)){ console.error(`no such file: ${file}`); process.exit(1); }
  const ffmpeg = findFfmpeg();
  const p = probe(ffmpeg, file);
  const bytes = statSync(file).size;

  // ---- G1 container ----------------------------------------------------
  gate("G1", "container", p.vcodec === "h264" && p.pixfmt === "yuv420p" && p.acodec === "aac",
       `${p.vcodec}/${p.profile} ${p.pixfmt} + ${p.acodec} ${p.audioRate}Hz ${p.channels}ch`);

  // ---- G2 geometry -----------------------------------------------------
  gate("G2", "geometry", p.width === SPEC.width && p.height === SPEC.height &&
       Math.abs(p.fps - SPEC.fps) < 0.01, `${p.width}x${p.height} @ ${p.fps}fps`);

  // ---- G3 duration -----------------------------------------------------
  const luma = lumaFrames(ffmpeg, file);
  const au = audioRms(ffmpeg, file);
  const vSec = luma.length / SPEC.fps;
  gate("G3", "duration",
       Math.abs(vSec - SPEC.seconds) <= SPEC.secondsTol &&
       Math.abs(vSec - au.seconds) <= SPEC.avSkew,
       `video ${vSec.toFixed(2)}s (${luma.length}f), audio ${au.seconds.toFixed(2)}s`);

  // ---- G4 size ---------------------------------------------------------
  gate("G4", "size", bytes <= SPEC.maxBytes, `${(bytes / 1e6).toFixed(2)} MB`);

  // ---- G5 not black ----------------------------------------------------
  let worst = {n: -1, frac: 0};
  for (let i = SPEC.openDark; i < luma.length - 6; i++){
    const f = luma[i];
    let dark = 0;
    for (let k = 0; k < f.length; k++) if (f[k] < SPEC.darkLuma) dark++;
    const frac = dark / f.length;
    if (frac > worst.frac) worst = {n: i, frac};
  }
  gate("G5", "not black", worst.frac < SPEC.darkFrac,
       `darkest frame ${worst.n} is ${(worst.frac * 100).toFixed(1)}% black`);

  // ---- G6 not frozen ---------------------------------------------------
  // The opening fade is black-on-black by design, and the title card is allowed to
  // hold still; everything between them has to be moving.
  let frozen = [];
  for (let i = SPEC.openDark; i < Math.min(luma.length, SPEC.tailFrom); i++)
    if (luma[i].equals(luma[i - 1])) frozen.push(i);
  gate("G6", "not frozen", frozen.length === 0,
       frozen.length ? `${frozen.length} still frames, first at ${frozen[0]}` : "no repeats");

  // ---- trace-backed gates ----------------------------------------------
  const tracePath = join(inDir, "trace.json");
  if (!existsSync(tracePath)){
    gate("G7", "hook", false, "no trace.json");
    gate("G8", "safe area", false, "no trace.json");
    gate("G9", "rules-true", false, "no trace.json");
  } else {
    const tr = JSON.parse(readFileSync(tracePath, "utf8"));
    const F = tr.frames;

    // G7: something readable is up almost immediately, and stays up long enough
    const firstCap = F.findIndex(f => f.capAlpha > 0.5);
    const spans = tr.spans.concat(
      F.at(-1).caption ? [{from: F.at(-1).n, to: F.at(-1).n, text: F.at(-1).caption}] : []);
    const hookSpan = spans[0];
    const hookLen = hookSpan ? hookSpan.to - hookSpan.from : 0;
    gate("G7", "hook", firstCap >= 0 && firstCap <= 12 && hookLen >= 45,
         `first legible caption at frame ${firstCap}, held ${hookLen} frames`);

    // G8: nothing important under the platform's own furniture
    const bad = F.filter(f => f.box && (f.box[0] < SPEC.safe.x0 || f.box[1] < SPEC.safe.y0 ||
                                        f.box[2] > SPEC.safe.x1 || f.box[3] > SPEC.safe.y1));
    gate("G8", "safe area", bad.length === 0,
         bad.length ? `${bad.length} frames outside, first ${JSON.stringify(bad[0].box)} @${bad[0].n}`
                    : `${F.filter(f => f.box).length} text frames all inside`);

    // G9: the clip's three factual claims, read off the sim's own state
    const marked = F.filter(f => f.marked);
    const claim1 = marked.every(f => f.holding !== null);          // aggro needs cargo
    const goals = new Set(marked.filter(f => f.goal).map(f => `${f.goal.hx},${f.goal.hz}`));
    const lastMarked = marked.at(-1);
    const reach = lastMarked && lastMarked.goal
      ? Math.hypot(lastMarked.cx - lastMarked.goal.hx, lastMarked.cz - lastMarked.goal.hz) : 99;
    const claim2 = goals.size === 1 && reach < 1.6;                // it paths to the plinth
    const lastHold = F.filter(f => f.holding !== null).at(-1);
    const clearedAt = lastHold ? F.find(f => f.n > lastHold.n && !f.marked) : null;
    const claim3 = !!clearedAt && (clearedAt.n - lastHold.n) <= 45; // 1.5s to go cold
    gate("G9", "rules-true", claim1 && claim2 && claim3,
         `marked-implies-carrying=${claim1}; single plinth goal reached at ` +
         `${reach.toFixed(2)}m=${claim2}; cleared ` +
         `${clearedAt && lastHold ? clearedAt.n - lastHold.n : "never"} frames after drop=${claim3}`);
  }

  // ---- G10 no drift ----------------------------------------------------
  let drift = "";
  let driftOk = false;
  try {
    drift = execFileSync("python3", [join(ROOT, "sim", "check_drift.py")],
                         {encoding: "utf8", cwd: ROOT});
    driftOk = /OK/.test(drift);
  } catch (e) { drift = String(e.stdout || e.message); }
  gate("G10", "no drift", driftOk, drift.trim().split("\n").pop());

  // ---- G11 audible on a phone -------------------------------------------
  // The bed shipped for eight rounds with 99% of its energy below 450 Hz, which is
  // to say silent on the device it was made for. Nothing but a measurement catches
  // that - "an audio stream exists" did not.
  const ph = audioRms(ffmpeg, file, PHONE);
  gate("G11", "audible", dbfs(ph.rms) >= SPEC.phoneRms && dbfs(au.peak) <= SPEC.peakMax,
       `phone-band ${dbfs(ph.rms).toFixed(1)} dBFS (min ${SPEC.phoneRms}), ` +
       `full-band peak ${dbfs(au.peak).toFixed(1)} dBFS (max ${SPEC.peakMax})`);

  // ---- report ----------------------------------------------------------
  const pad = s => String(s).padEnd(12);
  console.log(`\n  ${file.replace(ROOT + "/", "")}`);
  console.log(`  ${"-".repeat(72)}`);
  for (const r of results)
    console.log(`  ${r.ok ? "PASS" : "FAIL"}  ${r.id.padEnd(4)}${pad(r.name)}${r.detail}`);
  const failed = results.filter(r => !r.ok);
  console.log(`  ${"-".repeat(72)}`);
  console.log(`  ${failed.length ? `${failed.length} GATE${failed.length > 1 ? "S" : ""} FAILED`
                                  : "PASS  all gates green - the clip is shippable"}\n`);
  process.exit(failed.length ? 1 : 0);
}

main();
