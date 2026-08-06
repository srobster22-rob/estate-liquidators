// Headless smoke test for the two browser prototypes.
//
// check_drift.py reads the prototypes as TEXT. That catches a literal that
// disagrees with tuning.json, but it cannot catch a constant that is correct
// and unused - which is exactly what R16 found: proto/index.html declared a
// loudness table entry for walking that nothing ever read, and both files
// applied the cursed-item floor as a bare `*2` the checker never looked at.
//
// So this loads each prototype in real Chromium, reads the live values out of
// the running scope, drives the loop for a few hundred frames, and asserts the
// constants are actually WIRED IN, not merely present.
//
//   npm i playwright   (browsers are preinstalled; do not run `playwright install`)
//   node tools/proto_smoke.mjs
//
// Exits non-zero on the first failed assertion.

import { chromium } from "playwright";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const T = JSON.parse(readFileSync(resolve(ROOT, "tuning.json"), "utf8"));

let failures = 0;
const ok = (label, cond, detail = "") => {
  if (cond) console.log(`  pass  ${label}`);
  else { failures++; console.log(`  FAIL  ${label}  ${detail}`); }
};
const near = (a, b) => Math.abs(a - b) < 1e-9;

// PW_CHROME lets a machine whose preinstalled Chromium build does not match the
// installed playwright package point at the binary it does have.
const browser = await chromium.launch(
  process.env.PW_CHROME ? { executablePath: process.env.PW_CHROME } : {});

for (const [name, file, hook] of [
  ["proto (2D)", "proto/index.html", "__game"],
  ["proto3d (first-person)", "proto3d/index.html", "__g"],
]) {
  console.log(`\n${name}  -  ${file}`);
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  await page.goto("file://" + resolve(ROOT, file));
  await page.waitForFunction((h) => !!window[h], hook);

  // Constants, read from the running scope rather than the source text.
  const live = await page.evaluate(() => ({
    floor: typeof FLOOR_PER_CURSED === "number" ? FLOOR_PER_CURSED : null,
    ruinK: RUIN_K, ruinExp: RUIN_EXP,
    impulse: IMPULSE, sustained: SUSTAINED, ratchet: RATCHET_END,
    fee: FEE, grade: GRADE_MULT, att: ATT_MULT, slots: VAN_SLOTS,
    appraise: APPRAISE_S, L,
  }));

  ok("cursed floor is canonical (+7/item, R9)",
     near(live.floor, T.disturbance.per_cursed_item_floor),
     `got ${live.floor}, want ${T.disturbance.per_cursed_item_floor}`);
  ok("ruin curve", near(live.ruinK, T.van.ruin_k) && near(live.ruinExp, T.van.ruin_exp));
  ok("impulse / sustained / ratchet",
     near(live.impulse, T.loudness_constants.impulse_disturbance_per_l) &&
     near(live.sustained, T.loudness_constants.sustained_disturbance_per_l) &&
     near(live.ratchet, T.disturbance.ratchet_end));
  ok("curse tables", ["clean", "tainted", "malignant"].every((g) =>
       near(live.fee[g], T.curse.ledger_fee[g]) &&
       near(live.grade[g], T.curse.value_multiplier[g]) &&
       near(live.att[g], T.curse.attention_multiplier[g])));
  ok("van slots and appraise time",
     live.slots === T.van.base_slots && near(live.appraise, T.night.appraise_seconds));
  ok("loudness table matches AUDIO-SPEC",
     near(live.L.sprint, T.loudness.sprint) &&
     near(live.L.appraise, T.loudness.appraise) &&
     near(live.L.drop, T.loudness.break_small));

  // The floor constant is WIRED IN, not just declared: put cursed cargo in the
  // van and watch the floor move by exactly the canonical step.
  const wired = await page.evaluate(() => {
    const before = floorNow();
    van.cargo.push({ grade: "malignant", value: 0 });
    const one = floorNow();
    van.cargo.push({ grade: "tainted", value: 0 });
    const two = floorNow();
    van.cargo.length = 0;
    return { step1: one - before, step2: two - one };
  });
  ok("floorNow() actually applies the constant per cursed item",
     near(wired.step1, T.disturbance.per_cursed_item_floor) &&
     near(wired.step2, T.disturbance.per_cursed_item_floor),
     `steps ${wired.step1} / ${wired.step2}`);

  // And it runs. 600 frames of sprinting is ten seconds of play.
  const ran = await page.evaluate((h) => {
    const g = window[h];
    g.reset();
    g.press("ShiftLeft", true);
    g.press("KeyW", true);
    g.press("ArrowRight", true);
    const s = g.step(600, 1 / 60);
    return { t: s.t, dist: s.dist, tier: s.tier, over: s.over };
  }, hook);
  ok("600 frames advance the clock", ran.t > 9 && ran.t < 11, `t=${ran.t}`);
  ok("sprinting raises Disturbance off zero", ran.dist > 0, `dist=${ran.dist}`);
  ok("no page errors", errors.length === 0, errors.slice(0, 3).join(" | "));

  await page.close();
}

await browser.close();
console.log(failures ? `\n${failures} failure(s)` : "\nOK  both prototypes run and agree with tuning.json");
process.exit(failures ? 1 : 0);
