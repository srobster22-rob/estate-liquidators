// Sum exactcov outputs: node bench/covsum.js file...
const fs = require('fs'); const by = {};
for (const f of process.argv.slice(2)) for (const l of fs.readFileSync(f, 'utf8').split('\n')) {
  const m = l.match(/^rem\s+(\d+)\s+moves (\d+)\s+fell back to MC (\d+).*ms p50 (\d+) max (\d+)/); if (!m) continue;
  const b = (by[m[1]] = by[m[1]] || { n: 0, f: 0, p50: [], max: 0 }); b.n += +m[2]; b.f += +m[3]; b.p50.push(+m[4]); b.max = Math.max(b.max, +m[5]);
}
console.log(Object.keys(by).sort((a, b) => b - a).map(k => `rem ${k}: fell back ${by[k].f}/${by[k].n} (${Math.round(100 * by[k].f / by[k].n)}%), ms p50~${Math.round(by[k].p50.reduce((a, b) => a + b, 0) / by[k].p50.length)} max ${by[k].max}`).join('\n'));
