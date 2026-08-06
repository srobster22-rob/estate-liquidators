// Dump the prototype's Disturbance trajectory for a scripted night.
//
// Every check in this repo so far compares NUMBERS - constants in files, numbers
// in tables. None of them compares BEHAVIOUR, and behaviour is where this
// project's most expensive bug lived: R12 found sustained noise being applied
// per FRAME instead of per SECOND, which made sprinting 60x too loud and pinned
// the meter to COLLECT within a few strides. Every constant involved was
// correct. A drift check would have passed it forever.
//
// So this drives the real prototype, through the real input handler, at a real
// frame rate, and prints the meter every second as JSON. sim/check_trajectory.py
// re-derives the same run from tuning.json and compares.
//
//   node tools/trace_dist.mjs        ->  {"dt":..., "samples":[[t,dist],...]}

import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const browser = await chromium.launch(
  process.env.PW_CHROME ? { executablePath: process.env.PW_CHROME } : {});
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
await page.goto("file://" + resolve(ROOT, "proto3d/index.html"));
await page.waitForFunction(() => !!window.__g);

const trace = await page.evaluate(() => {
  const g = window.__g;
  g.reset();
  const DT = 1 / 60;
  const out = [];
  const sample = () => out.push([+t.toFixed(4), +dist.toFixed(6)]);

  // Phase A - five seconds of sprinting. Stamina lasts six, so the sprint runs
  // the whole phase and the sustained-noise path is exercised every frame.
  g.press("ShiftLeft", true);
  g.press("KeyW", true);
  for (let i = 0; i < 300; i++) { g.step(1, DT); if (i % 60 === 59) sample(); }

  // Phase B - five seconds of standing still. Decay, floored by the ratchet.
  g.press("ShiftLeft", false);
  g.press("KeyW", false);
  for (let i = 0; i < 300; i++) { g.step(1, DT); if (i % 60 === 59) sample(); }

  // Phase C - three impulses two seconds apart, straight at the integrator.
  for (let k = 0; k < 3; k++) {
    noise(L.drop, true, 0);
    for (let i = 0; i < 120; i++) { g.step(1, DT); if (i % 60 === 59) sample(); }
  }
  return { dt: DT, samples: out };
});

await browser.close();
if (errors.length) {
  console.error(JSON.stringify({ errors }));
  process.exit(1);
}
console.log(JSON.stringify(trace));
