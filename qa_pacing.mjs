// R30 — does the prototype independently price R29's room decision?
// R29 (Python, Monte Carlo) says: scan selectively and stay safe, scan everything and
// get hunted. proto/index.html is a real-time JS implementation that shares no code with
// it. If the same decision shows up here, that is two independent routes to one finding.
import { chromium } from 'playwright';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
const p = await b.newPage();
await p.goto('file:///home/user/estate-liquidators/proto/index.html');
await p.waitForFunction(() => window.__game);

const out = await p.evaluate(() => {
  const g = window.__game;
  // How many items live in each room class, from the estate the prototype actually ships.
  g.reset();
  const byRoom = {};
  for (const it of g.raw()) (byRoom[it.room] ??= 0), byRoom[it.room]++;
  const spreads = Object.fromEntries(g.spreads().map(r => [r.room, r.spread]));
  const count = cls => Object.entries(byRoom)
    .filter(([r]) => cls.includes(spreads[r])).reduce((s, [, n]) => s + n, 0);

  const plans = [
    { label: 'nothing',            n: 0 },
    { label: 'curio only',         n: count(['curio']) },
    { label: 'curio + mixed',      n: count(['curio', 'mixed']) },
    { label: 'everything',         n: count(['curio', 'mixed', 'uniform']) },
  ];
  const rows = [];
  for (const plan of plans) {
    g.reset();
    // Spread the scans evenly across the night, as a crew working room by room would.
    const gap = plan.n ? Math.floor(60 * 180 / plan.n) : Infinity;
    let peak = 0, collect = 0, frames = 0;
    for (let f = 0; f < 60 * 180; f++) {
      g.step(1);
      if (plan.n && f % gap === 0) g.noise(48, true);
      const s = g.state();
      peak = Math.max(peak, s.dist);
      if (s.tier === 'COLLECT') collect++;
      frames++;
      if (s.over) break;
    }
    const s = g.state();
    rows.push({ ...plan, scansPerMin: (plan.n / 3).toFixed(1), peak: Math.round(peak),
                tier: s.tier, collectPct: Math.round(100 * collect / frames) });
  }
  return { rows, byRoom, spreads };
});

console.log('R30 — the prototype prices the room decision. Estate as shipped:');
for (const [r, n] of Object.entries(out.byRoom))
  console.log(`   ${r.padEnd(7)} ${String(n).padStart(2)} items   ${out.spreads[r] ?? 'n/a'}`);
console.log('\nscan plan          items  scans/min   peak D   end tier   % of night in COLLECT');
for (const r of out.rows)
  console.log(`${r.label.padEnd(18)}${String(r.n).padStart(5)}${String(r.scansPerMin).padStart(11)}`
    + `${String(r.peak).padStart(9)}   ${r.tier.padEnd(10)} ${r.collectPct}%`);
await b.close();
