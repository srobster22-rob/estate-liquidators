// Parallel benchmark + paired A/B comparison.
//
//   node bench/par.js --html=index.html --games=400
//   node bench/par.js --a=index.html --b=cand.html --games=400
//
// Paired design: both variants play the SAME shuffled decks and the SAME internal
// Math.random stream, so the comparison is on paired differences. That kills most
// of the ~2400-point per-game variance and makes a 50-point edge measurable.
const path = require('path');
const os = require('os');
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');

if (!isMainThread) {
  const { loadEngine } = require('./engine');
  const { playGame, mulberry32 } = require('./game');
  const E = loadEngine(workerData.html);
  const out = [];
  for (const seed of workerData.seeds) {
    // Deterministic internal randomness: same seed => same rollout sampling.
    const r = mulberry32(seed ^ 0x9e3779b9);
    Math.random = r;
    out.push({ seed, ...playGame(E, seed, { mode: workerData.mode, target: workerData.target }) });
  }
  parentPort.postMessage(out);
} else {
  const args = Object.fromEntries(process.argv.slice(2)
    .filter(a => a.startsWith('--'))
    .map(a => { const i = a.indexOf('='); return i < 0 ? [a.slice(2), true] : [a.slice(2, i), a.slice(i + 1)]; }));

  const games = parseInt(args.games || '200', 10);
  const seed0 = parseInt(args.seed || '1000', 10);
  const mode = args.mode || 'balanced';
  const target = parseInt(args.target || '0', 10);
  const nw = parseInt(args.workers || String(Math.max(1, Math.min(22, os.cpus().length - 2))), 10);
  const resolveHtml = h => path.resolve(__dirname, '..', h);

  const seeds = Array.from({ length: games }, (_, i) => seed0 + i);

  function runOne(html) {
    const chunks = Array.from({ length: nw }, () => []);
    seeds.forEach((s, i) => chunks[i % nw].push(s));
    return Promise.all(chunks.filter(c => c.length).map(c => new Promise((res, rej) => {
      const w = new Worker(__filename, { workerData: { html, seeds: c, mode, target } });
      w.on('message', m => res(m));
      w.on('error', rej);
    }))).then(all => {
      const rows = [].concat(...all);
      rows.sort((x, y) => x.seed - y.seed);
      return rows;
    });
  }

  const stats = rows => {
    const n = rows.length;
    const f = rows.map(r => r.final).sort((a, b) => a - b);
    const mean = f.reduce((a, b) => a + b, 0) / n;
    const sd = Math.sqrt(f.reduce((a, b) => a + (b - mean) ** 2, 0) / Math.max(1, n - 1));
    const q = p => f[Math.min(n - 1, Math.floor(p * n))];
    const avg = k => rows.reduce((a, r) => a + r[k], 0) / n;
    return {
      games: n, mean: +mean.toFixed(1), stderr: +(sd / Math.sqrt(n)).toFixed(1), sd: +sd.toFixed(0),
      p10: q(0.1), median: q(0.5), p90: q(0.9), max: f[n - 1],
      perfect: +(rows.filter(r => r.lives >= 3).length / n).toFixed(3),
      bustOut: +(rows.filter(r => r.lives <= 0).length / n).toFixed(3),
      cashOut: +(rows.filter(r => r.cashedOut).length / n).toFixed(3),
      forfeit: +(rows.filter(r => r.forfeited).length / n).toFixed(3),
      busts: +avg('busts').toFixed(2), forcedBusts: +avg('forcedBusts').toFixed(2), n21: +avg('win21').toFixed(2), n5: +avg('win5').toFixed(2),
      n5x21: +avg('win5x21').toFixed(2), n777: +avg('win777').toFixed(3),
      psd: +avg('passes').toFixed(2), maxStreak: +avg('maxStreak').toFixed(2),
      beatRate: target > 0 ? +(rows.filter(r => r.final > target).length / n).toFixed(3) : null,
      chainBonus: +avg('chainBonus').toFixed(0), clears: +avg('clears').toFixed(2),
      chains: [1, 2, 3, 4].map(k => +(rows.reduce((a, r) => a + r.chainHist[k], 0) / n).toFixed(2))
    };
  };

  (async () => {
    const t0 = Date.now();
    if (args.a && args.b) {
      const [ra, rb] = await Promise.all([runOne(resolveHtml(args.a)), runOne(resolveHtml(args.b))]);
      const d = ra.map((r, i) => rb[i].final - r.final);
      const n = d.length;
      const dm = d.reduce((a, b) => a + b, 0) / n;
      const dsd = Math.sqrt(d.reduce((a, b) => a + (b - dm) ** 2, 0) / Math.max(1, n - 1));
      const se = dsd / Math.sqrt(n);
      console.log(JSON.stringify({
        A: { html: args.a, ...stats(ra) },
        B: { html: args.b, ...stats(rb) },
        paired: {
          deltaMean: +dm.toFixed(1), stderr: +se.toFixed(1),
          t: +(dm / (se || 1e-9)).toFixed(2),
          ci95: [+(dm - 1.96 * se).toFixed(1), +(dm + 1.96 * se).toFixed(1)],
          bWins: d.filter(x => x > 0).length, aWins: d.filter(x => x < 0).length, ties: d.filter(x => x === 0).length
        },
        secs: +((Date.now() - t0) / 1000).toFixed(1)
      }, null, 2));
      if (args.json) require('fs').writeFileSync(args.json, JSON.stringify({ ra, rb }, null, 2));
    } else {
      const rows = await runOne(resolveHtml(args.html || 'index.html'));
      const s = stats(rows);
      console.log(JSON.stringify({ html: args.html || 'index.html', mode, ...s,
        secs: +((Date.now() - t0) / 1000).toFixed(1) }, null, 2));
      if (args.json) require('fs').writeFileSync(args.json, JSON.stringify({ summary: s, rows }, null, 2));
    }
  })();
}
