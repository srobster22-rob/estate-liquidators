// ===========================================================================
// clip/encode.mjs - frames + synthesized bed -> the uploadable mp4.
//
// Also where the grade lives. The prototype renders one flashlight against near-
// black, which is correct for the game and unwatchable on a phone in daylight: the
// whole picture sits in the bottom 15% of the range. The curve below expands the
// low-mids hard while pinning true black at 0, so the dark stays dark and the lit
// surfaces come up. It is a grade, not a lighting change - the game is untouched.
//
//   node clip/encode.mjs [--in clip/build] [--out clip/build/estate-liquidators.mp4]
// ===========================================================================
import {execFileSync, execSync} from "node:child_process";
import {existsSync, readdirSync, statSync} from "node:fs";
import {dirname, join, resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {write as writeBed} from "./audio.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf("--" + n); return i >= 0 ? argv[i + 1] : d; };

export const FPS = 30;
// The grade. Control points are (input, output) in normalised luma.
export const GRADE =
  "curves=all='0/0 0.035/0.012 0.12/0.175 0.30/0.50 0.60/0.82 1/1'," +
  "eq=saturation=1.10:contrast=1.04";

// ffmpeg hunt: an explicit override, then PATH, then the one imageio-ffmpeg ships.
// Playwright's bundled build is deliberately not used - it has no libx264.
export function findFfmpeg(){
  const tries = [];
  if (process.env.FFMPEG) tries.push(process.env.FFMPEG);
  tries.push("ffmpeg");
  try {
    tries.push(execSync(
      "python3 -c \"import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())\"",
      {encoding: "utf8", stdio: ["ignore", "pipe", "ignore"]}).trim());
  } catch { /* not installed; fine */ }

  for (const bin of tries){
    if (!bin) continue;
    try {
      const out = execFileSync(bin, ["-hide_banner", "-encoders"],
                               {encoding: "utf8", stdio: ["ignore", "pipe", "ignore"]});
      if (out.includes("libx264") && out.includes(" aac ")) return bin;
    } catch { /* try the next one */ }
  }
  throw new Error(
    "no ffmpeg with libx264 + aac found. Install ffmpeg, or `pip install imageio-ffmpeg`, " +
    "or set FFMPEG=/path/to/ffmpeg.");
}

function run(bin, args){
  execFileSync(bin, args, {stdio: ["ignore", "ignore", "inherit"]});
}

export function encode({inDir, out, fps = FPS}){
  const frames = join(inDir, "frames");
  const n = readdirSync(frames).filter(f => f.endsWith(".png")).length;
  if (!n) throw new Error(`no frames in ${frames} - run clip/render.mjs first`);

  const bed = join(inDir, "bed.wav");
  const seconds = n / fps;
  writeBed(bed, seconds);

  const ffmpeg = findFfmpeg();
  run(ffmpeg, [
    "-y", "-hide_banner", "-loglevel", "error",
    "-framerate", String(fps), "-i", join(frames, "%05d.png"),
    "-i", bed,
    "-filter_complex", `[0:v]${GRADE},format=yuv420p[v]`,
    "-map", "[v]", "-map", "1:a",
    "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "19",
    "-x264-params", "keyint=60:min-keyint=30:scenecut=0",
    "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
    "-shortest", "-movflags", "+faststart",
    out
  ]);
  return {out, frames: n, seconds, bytes: statSync(out).size, ffmpeg};
}

if (import.meta.url === `file://${process.argv[1]}`){
  const inDir = resolve(ROOT, arg("in", "clip/build"));
  const out = resolve(ROOT, arg("out", "clip/estate-liquidators.mp4"));
  if (!existsSync(inDir)) throw new Error(`${inDir} does not exist`);
  const r = encode({inDir, out});
  console.log(`  encoded ${r.frames} frames (${r.seconds.toFixed(2)}s) -> ${r.out}`);
  console.log(`  size    ${(r.bytes / 1e6).toFixed(2)} MB   via ${r.ffmpeg}`);
}
