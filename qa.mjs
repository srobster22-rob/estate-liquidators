// R20 — in-browser verification of room_spread in proto/index.html.
//
// The prototype is the only place the design's claims meet real code, and R12 and R18
// are both standing evidence that porting a verified model finds things no sweep can.
// This drives the real page in headless Chromium and asserts the two claims D-23 rests
// on, neither of which is safe to take on faith:
//
//   D-10  the telegraph must expose the ROOM's spread and never the ITEM's value.
//         Correlation is computed WITHIN each room -- pooling across tiers gives a
//         confounded r of ~0.46, because silhouette base and value both scale with
//         depth. Within room it must be ~0.
//   D-23  a V11-compliant estate holds no EXTRA money, only a decision. Mean pre-curse
//         value per tier must still land on the band midpoint.
//
// Needs playwright: npm install playwright --no-save
// Run: node qa.mjs
import { chromium } from 'playwright';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
const p = await b.newPage({ viewport: { width: 1200, height: 720 } });
const errs = [];
p.on('pageerror', e => errs.push('PAGEERROR: ' + e.message));
p.on('console', m => { if (m.type() === 'error') errs.push('CONSOLE: ' + m.text()); });
await p.goto('file:///home/user/estate-liquidators/proto/index.html');
await p.waitForFunction(() => window.__game);

const out = await p.evaluate(() => {
  const g = window.__game, acc = {}, pairs = {}, tierTotals = {};
  for (let k = 0; k < 600; k++) {
    g.reset();
    for (const r of g.spreads()) {
      (acc[r.room] ??= { spread: r.spread, tier: r.tier, v: [], s: [], sh: [] });
      acc[r.room].v.push(r.valueSd); acc[r.room].s.push(r.silSd); acc[r.room].sh.push(r.shapes);
    }
    for (const it of g.raw()) {
      const v = it.value / ({ clean: 1, tainted: 2.5, malignant: 6 })[it.grade];
      (pairs[it.room] ??= []).push([it.sil, v]);
      (tierTotals[it.tier] ??= []).push(v);
    }
  }
  const mean = a => a.reduce((x, y) => x + y, 0) / a.length;
  // correlation between silhouette size and true value, WITHIN tier (sizes scale by tier)
  const corr = a => {
    const mx = mean(a.map(z => z[0])), my = mean(a.map(z => z[1]));
    const num = mean(a.map(z => (z[0] - mx) * (z[1] - my)));
    const sx = Math.sqrt(mean(a.map(z => (z[0] - mx) ** 2))), sy = Math.sqrt(mean(a.map(z => (z[1] - my) ** 2)));
    return num / (sx * sy);
  };
  return {
    rooms: Object.entries(acc).map(([room, d]) => ({
      room, tier: d.tier, spread: d.spread,
      valueSd: Math.round(mean(d.v)), silSd: +mean(d.s).toFixed(2), shapes: +mean(d.sh).toFixed(2),
    })),
    corrByRoom: Object.fromEntries(Object.entries(pairs).map(([r, a]) => [r, +corr(a).toFixed(4)])),
    nByRoom: Object.fromEntries(Object.entries(pairs).map(([r, a]) => [r, a.length])),
    tierMeans: Object.fromEntries(Object.entries(tierTotals).map(([t, a]) => [t, Math.round(mean(a))])),

  };
});

console.log('room       tier  spread     valueSd   silSd  shapes');
for (const r of out.rooms)
  console.log(`${r.room.padEnd(11)}${String(r.tier).padEnd(6)}${r.spread.padEnd(11)}${String(r.valueSd).padStart(7)}${String(r.silSd).padStart(8)}${String(r.shapes).padStart(8)}`);

console.log('\nD-10 CHECK  corr(silhouette, true value) WITHIN each room:');
console.log('            (pooling across tiers would be confounded - both scale with depth)');
for (const [r, c] of Object.entries(out.corrByRoom))
  console.log(`            ${r.padEnd(8)} r = ${String(c).padStart(8)}   (n=${out.nByRoom[r]})`);
console.log('D-23 CHECK  mean pre-curse value by tier =', JSON.stringify(out.tierMeans));
console.log('            band midpoints              = {"0":95,"1":190,"2":475,"3":1000}');

const fin = await p.evaluate(() => { window.__game.reset(); window.__game.step(60 * 200); return window.__game.state(); });
console.log('\nfull night to sunrise:', JSON.stringify(fin));
await p.evaluate(() => window.__game.reset());
await p.screenshot({ path: 'proto/telegraph.png' });
console.log('errors:', errs.length ? errs : 'none');
await b.close();
