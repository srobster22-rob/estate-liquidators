// ===========================================================================
// clip/build.mjs - one command: capture, encode, gate.
//
//   node clip/build.mjs                 full 24s build, then checks
//   node clip/build.mjs --frames 90     a quick look at the first 3 seconds
//   node clip/build.mjs --skip-render   re-encode and re-check existing frames
// ===========================================================================
import {spawnSync} from "node:child_process";
import {mkdirSync} from "node:fs";
import {dirname, join, resolve} from "node:path";
import {fileURLToPath} from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf("--" + n); return i >= 0 ? argv[i + 1] : d; };
const has = n => argv.includes("--" + n);

const outDir = resolve(ROOT, arg("out", "clip/build"));
const frames = arg("frames", "720");
const seed = arg("seed", "20260806");
// Intermediates (frames, bed, trace) live in the ignored build dir; the finished
// clip lands beside its source so a clone can watch it without rendering first.
const mp4 = resolve(ROOT, arg("mp4", "clip/estate-liquidators.mp4"));
mkdirSync(outDir, {recursive: true});

const step = (label, args) => {
  console.log(`\n${label}`);
  const r = spawnSync(process.execPath, args, {stdio: "inherit", cwd: ROOT});
  if (r.status !== 0 && label !== "gate") process.exit(r.status ?? 1);
  return r.status ?? 1;
};

if (!has("skip-render"))
  step("capture", [join(HERE, "render.mjs"), "--frames", frames, "--seed", seed,
                   "--out", outDir]);
step("encode", [join(HERE, "encode.mjs"), "--in", outDir, "--out", mp4]);
const status = step("gate", [join(HERE, "check.mjs"), "--in", outDir, "--file", mp4]);
process.exit(status);
