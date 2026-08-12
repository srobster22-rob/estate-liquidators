import indexData from './generated/index.json';
import type { DataIndex, GapAnswer, GapState, SourceRef } from './types.js';
import { assessGaps, rentersNote, waitingPeriod } from './coverage.js';
import {
  appendEntry, verifyChain, describeTimestamp, makePhotoRecord, hashBytes, METHODOLOGY,
  entryKind, formatCents, parseMoneyToCents, receiptsTotalCents, countByKind,
  type ChainEntry, type PhotoRecord,
} from './evidence.js';
import { loadChain, saveChain, putBlob, storageReport, StorageUnavailableError } from './store.js';

const data = indexData as unknown as DataIndex;

function esc(s: string): string {
  return s.replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!);
}

function sourceList(sources: SourceRef[]): string {
  if (!sources.length) return '';
  return `<ul class="plain sources">${sources
    .map((s) => `<li>${esc(s.org)}, <a href="${esc(s.url)}" rel="noopener">${esc(s.title)}</a>
      — checked ${esc(s.retrieved)}${s.method === 'search_index' ? ' (via search index, not fetched)' : ''}</li>`)
    .join('')}</ul>`;
}

// ------------------------------------------------------------------ answers (session only)

const ANSWER_KEY = 'fw.answers';
type Answers = { tenure?: 'own' | 'rent'; gaps: Record<string, GapState>; exceptions: string[] };

function readAnswers(): Answers {
  try {
    return { gaps: {}, exceptions: [], ...JSON.parse(sessionStorage.getItem(ANSWER_KEY) ?? '{}') };
  } catch {
    return { gaps: {}, exceptions: [] };
  }
}
function writeAnswers(a: Answers): void {
  try { sessionStorage.setItem(ANSWER_KEY, JSON.stringify(a)); } catch { /* ignore */ }
}

// ------------------------------------------------------------------ screens

function renderCoverage(): string {
  const a = readAnswers();
  const verdicts = assessGaps(data.coverage, Object.entries(a.gaps).map(
    ([gapId, state]): GapAnswer => ({ gapId, state })));
  const wp = waitingPeriod(data.coverage, new Date(), a.exceptions);

  const questions = data.coverage.gaps.map((g) => `
    <fieldset class="q">
      <legend>${esc(g.name)}</legend>
      <p>${esc(g.what)}</p>
      <label><input type="radio" name="gap-${g.id}" value="yes" ${a.gaps[g.id] === 'yes' ? 'checked' : ''}> I have it</label>
      <label><input type="radio" name="gap-${g.id}" value="no" ${a.gaps[g.id] === 'no' ? 'checked' : ''}> I don't have it</label>
      <label><input type="radio" name="gap-${g.id}" value="unknown" ${(a.gaps[g.id] ?? 'unknown') === 'unknown' ? 'checked' : ''}> I don't know</label>
    </fieldset>`).join('');

  const results = verdicts.map((v) => {
    const cls = v.isGap ? 'gap-missing' : v.needsChecking ? 'gap-unknown' : 'gap-have';
    const head = v.isGap ? 'Not covered' : v.needsChecking ? 'Worth checking' : 'Covered';
    return `
      <div class="gap-row ${cls}">
        <p><strong>${esc(head)} — ${esc(v.gap.name)}</strong></p>
        <p>${esc(v.gap.why)}</p>
        ${v.needsChecking ? `<p><strong>How to check:</strong> ${esc(v.lookFor)}</p>` : ''}
        ${v.gap.id === 'flood' && a.tenure === 'rent' && rentersNote(data.coverage)
          ? `<p><strong>${esc(rentersNote(data.coverage)!)}</strong></p>` : ''}
        ${sourceList(v.sources)}
      </div>`;
  }).join('');

  const exceptionQs = data.coverage.waitingPeriod.exceptions.map((e) => `
    <label><input type="checkbox" name="exc" value="${e.id}" ${a.exceptions.includes(e.id) ? 'checked' : ''}>
      ${esc(e.question)}</label>`).join('');

  return `
    <h1>Am I covered?</h1>
    <p>Four questions. Nothing is sent anywhere and nothing is saved when you close the tab.</p>

    <fieldset class="q">
      <legend>Do you own or rent?</legend>
      <label><input type="radio" name="tenure" value="own" ${a.tenure === 'own' ? 'checked' : ''}> I own</label>
      <label><input type="radio" name="tenure" value="rent" ${a.tenure === 'rent' ? 'checked' : ''}> I rent</label>
    </fieldset>
    ${questions}

    <h2>What that means</h2>
    ${results}

    <h2>If you bought flood coverage today</h2>
    <div class="verdict">
      <p>Coverage would start</p>
      <p class="bigdate">${esc(wp.effectiveOn)}</p>
      <p class="verdict-sub">${esc(wp.detail)}</p>
      <p class="verdict-sub"><strong>Buying while a storm is coming does not work.</strong>
        This decision has to be made on a dry day.</p>
    </div>
    <details>
      <summary>Some situations have a shorter or no waiting period</summary>
      <div class="q">${exceptionQs}</div>
    </details>
    ${sourceList(wp.sources)}

    <p class="meta-line">Data built ${esc(data.builtAt)}. This is not insurance advice and not a
      coverage determination — only your insurer can tell you what your policy covers.</p>`;
}

function renderNow(): string {
  const e = data.safety.emergency;
  return `
    <div class="emergency">
      <h1>${esc(e.headline)}</h1>
      <ul class="plain">${e.points.map((p) => `<li>${esc(p.text)}</li>`).join('')}</ul>
      <p><strong>If someone is in danger, call 911.</strong></p>
    </div>
    <h2>Once you are safe</h2>
    <ul class="plain">
      <li>Photograph everything <strong>before</strong> you move or clean anything. Wide shot of
        each room, then the water line on the walls, then close-ups.</li>
      <li>Keep every receipt — pumps, fans, a hotel, a plumber.</li>
      <li>Call your insurer and write down who you spoke to and when.</li>
      <li>${esc(data.safety.mold.text)}</li>
    </ul>
    ${sourceList([...e.points.flatMap((p) => p.sources), ...data.safety.mold.sources]
      .filter((s, i, arr) => arr.findIndex((x) => x.url === s.url) === i))}
    <p><a class="btn" href="#/log">Start a damage record</a></p>`;
}

function renderPrepare(): string {
  return `
    <h1>Before it happens</h1>
    <p>Ordered by what protects the most for the least effort.</p>
    ${data.safety.prepare.map((s, i) => `
      <div class="place">
        <p class="place-name">${i + 1}. ${esc(s.title)}</p>
        <p>${esc(s.detail)}</p>
        <p class="place-meta">Cost: ${esc(s.cost)}</p>
        ${sourceList(s.sources)}
      </div>`).join('')}`;
}

// ------------------------------------------------------------------ damage log

let chain: ChainEntry[] = [];
/** Entries held only in memory because the device refused to save them. */
let unsavedCount = 0;

/** One human line per entry, whatever kind it is. */
function describeEntry(b: Record<string, unknown>): string {
  switch (entryKind(b)) {
    case 'damage':
      return `Damaged — ${b.room}: ${b.description}` +
        (b.purchaseCostCents ? ` (cost ${formatCents(Number(b.purchaseCostCents))}` +
          `${b.purchaseYear ? ` in ${b.purchaseYear}` : ''}, ${b.condition})` : ` (${b.condition})`);
    case 'call':
      return `Call — ${b.party}${b.person ? `, spoke to ${b.person}` : ''}` +
        `${b.claimNumber ? ` (claim ${b.claimNumber})` : ''}: ${b.summary}` +
        `${b.promised ? ` — promised: ${b.promised}` : ''}`;
    case 'receipt':
      return `Paid ${formatCents(Number(b.amountCents))} to ${b.vendor} on ${b.datedOn} (${b.category})`;
    default:
      return String(b.note ?? '');
  }
}

/** Counts, and the receipts total — never a damage total. See receiptsTotalCents(). */
function summaryLine(entries: ChainEntry[]): string {
  const n = countByKind(entries);
  const total = receiptsTotalCents(entries);
  if (!entries.length) return '';
  const bits = [
    `${n.note} note${n.note === 1 ? '' : 's'}`,
    `${n.damage} damaged item${n.damage === 1 ? '' : 's'}`,
    `${n.call} call${n.call === 1 ? '' : 's'}`,
    `${n.receipt} receipt${n.receipt === 1 ? '' : 's'}`,
  ].join(' · ');
  return `<p class="place-meta">${bits}${
    n.receipt ? ` · <strong>${esc(formatCents(total))}</strong> in receipts recorded` : ''
  }</p>
  ${n.receipt ? '<p class="place-meta">That is what you have spent and kept paper for. It is not an estimate of what you are owed.</p>' : ''}`;
}

async function renderLog(): Promise<string> {
  // Only re-read from storage when nothing is being held in memory, or a failed save would be
  // undone by the next render and the entry really would disappear.
  if (unsavedCount === 0) chain = await loadChain();
  const check = await verifyChain(chain);
  const report = await storageReport();

  const entries = chain.length
    ? chain.map((e) => {
        const b = e.body as Record<string, unknown>;
        const photo = b.photo as PhotoRecord | undefined;
        return `
        <div class="entry ${e.correctsSeq ? 'correction' : ''}">
          ${e.correctsSeq ? `<p class="entry-meta">Correction to entry #${e.correctsSeq}</p>` : ''}
          <p>${esc(describeEntry(b))}</p>
          ${photo ? `<p class="entry-meta">${esc(describeTimestamp(photo))}</p>
            <p class="entry-meta">SHA-256 ${esc(photo.sha256.slice(0, 16))}… · ${photo.byteSize} bytes</p>` : ''}
          <p class="entry-meta">#${e.seq} · recorded ${esc(e.createdAt)} · hash ${esc(e.contentHash.slice(0, 12))}…</p>
        </div>`;
      }).join('')
    : '<p>Nothing recorded yet.</p>';

  const unsavedBanner = unsavedCount > 0
    ? `<div class="callout callout-danger"><p><strong>${unsavedCount}
        ${unsavedCount === 1 ? 'entry is' : 'entries are'} not saved on this device.</strong>
        Save the PDF now — closing this tab will lose ${unsavedCount === 1 ? 'it' : 'them'}.</p></div>`
    : '';

  return `
    <h1>Damage record</h1>
    ${unsavedBanner}
    <p>Everything stays on this device. Entries cannot be edited — a change adds a correction and
      both stay visible, which is what makes the record worth anything.</p>

    <div class="q">
      <label for="note"><strong>Add a note</strong></label>
      <input type="text" id="note" placeholder="Water reached the third step, 6:40am" />
      <p><label for="photo"><strong>Attach a photo</strong> (optional)</label>
      <input type="file" id="photo" accept="image/*" /></p>
      <p><button class="btn" id="add">Add to record</button></p>
    </div>

    <details class="q"><summary><strong>Something that was damaged</strong></summary>
      <p><label for="d-room">Room</label><input type="text" id="d-room" placeholder="Basement" /></p>
      <p><label for="d-desc">What it is</label><input type="text" id="d-desc" placeholder="Sofa" /></p>
      <p><label for="d-cost">What it cost when you bought it</label>
        <input type="text" id="d-cost" placeholder="900" inputmode="decimal" /></p>
      <p><label for="d-year">Year bought</label><input type="text" id="d-year" placeholder="2019" inputmode="numeric" /></p>
      <p><label for="d-cond">Condition</label>
        <select id="d-cond">
          <option value="ruined">Ruined</option>
          <option value="damaged">Damaged</option>
          <option value="maybe-dryable">Might dry out</option>
          <option value="unknown">Not sure</option>
        </select></p>
      <p><button class="btn" data-add="damage">Add this item</button></p>
      <p class="place-meta">What it cost when you bought it — not what it is worth now. This app
        does not put a value on anything; the adjuster does that.</p>
    </details>

    <details class="q"><summary><strong>A call you made</strong></summary>
      <p><label for="c-party">Who you called</label><input type="text" id="c-party" placeholder="Insurance company" /></p>
      <p><label for="c-person">Who you spoke to</label><input type="text" id="c-person" placeholder="Rita" /></p>
      <p><label for="c-claim">Claim number, if they gave one</label><input type="text" id="c-claim" /></p>
      <p><label for="c-summary">What was said</label><input type="text" id="c-summary" placeholder="Adjuster booked for Thursday" /></p>
      <p><label for="c-promised">What they promised</label><input type="text" id="c-promised" /></p>
      <p><button class="btn" data-add="call">Add this call</button></p>
    </details>

    <details class="q"><summary><strong>Something you paid for</strong></summary>
      <p><label for="r-vendor">Who you paid</label><input type="text" id="r-vendor" placeholder="Hardware store" /></p>
      <p><label for="r-amount">How much</label><input type="text" id="r-amount" placeholder="89.99" inputmode="decimal" /></p>
      <p><label for="r-date">Date</label><input type="date" id="r-date" /></p>
      <p><label for="r-cat">What for</label>
        <select id="r-cat">
          <option value="drying">Drying out / pumps / fans</option>
          <option value="repair">Repair</option>
          <option value="lodging">Somewhere to stay</option>
          <option value="meals">Meals</option>
          <option value="other">Something else</option>
        </select></p>
      <p><button class="btn" data-add="receipt">Add this receipt</button></p>
      <p class="place-meta">Keep the paper too. Extra living costs are often reimbursable and
        often unclaimed because nobody kept the receipts.</p>
    </details>

    <p><button class="btn btn-secondary" id="export">Save as a PDF for your insurer</button>
      <button class="btn btn-secondary" id="export-zip">Save the original photo files</button></p>
    <p class="place-meta">The PDF is for reading. The photo files are for checking: they come out
      exactly as they went in, with a manifest an adjuster can re-hash them against.</p>

    ${summaryLine(chain)}

    <p>Chain: <span class="${check.intact ? 'chain-ok' : 'chain-broken'}">
      ${chain.length} ${chain.length === 1 ? 'entry' : 'entries'},
      ${check.intact ? 'intact' : `BROKEN at #${check.brokenAt} (${esc(check.reason ?? '')})`}
    </span></p>
    <p class="place-meta">${esc(report)}</p>

    ${entries}

    <h2>What this record proves</h2>
    <pre class="sources" style="white-space:pre-wrap">${esc(METHODOLOGY)}</pre>`;
}

async function addLogEntry(): Promise<void> {
  const noteEl = document.getElementById('note') as HTMLInputElement;
  const fileEl = document.getElementById('photo') as HTMLInputElement;
  const note = noteEl.value.trim();
  const file = fileEl.files?.[0];
  if (!note && !file) return;

  const createdAt = new Date().toISOString();
  let photo: PhotoRecord | undefined;

  if (file) {
    const bytes = new Uint8Array(await file.arrayBuffer());
    // Hash the ORIGINAL bytes before anything touches them, and store them unmodified.
    const sha256 = await hashBytes(bytes);
    let exifDateTimeOriginal: string | null = null;
    try {
      const exifr = await import('exifr');
      const parsed = await exifr.parse(file, ['DateTimeOriginal']);
      const d = parsed?.DateTimeOriginal;
      if (d instanceof Date && !Number.isNaN(d.getTime())) {
        exifDateTimeOriginal = d.toISOString().replace('T', ' ').slice(0, 19);
      }
    } catch {
      // No EXIF, or an unreadable container. That is a real answer, not an error: the record
      // will say "no camera timestamp" rather than pretending the import time is a capture time.
    }
    try {
      await putBlob(sha256, bytes);
    } catch (err) {
      alert(
        'Could not save the photo — this device is out of storage space for this site. ' +
          'Export what you have, or remove some photos, then try again.',
      );
      throw err;
    }
    photo = makePhotoRecord({
      sha256, byteSize: bytes.byteLength, mime: file.type || 'application/octet-stream',
      exifDateTimeOriginal, importedAt: createdAt.slice(0, 10),
    });
  }

  chain = [...chain, await appendEntry(chain, { note, ...(photo ? { photo } : {}) }, createdAt)];
  try {
    await saveChain(chain);
  } catch (err) {
    if (!(err instanceof StorageUnavailableError)) throw err;
    // Keep it in memory so it can still be exported, and say so plainly. An entry that looks
    // saved and is not is the worst outcome this screen can produce.
    unsavedCount++;
    alert(
      'This device would not save the record — it may be out of space, or this may be a private ' +
        'window. The entry is still here for now. Save the PDF before you close this tab.',
    );
  }
  await route();
}

function renderAbout(): string {
  return `
    <h1>About this</h1>
    <h2>The three things this exists to say</h2>
    <ol class="plain">
      <li>Standard homeowners and renters insurance does not cover flood. Flood is a separate
        policy.</li>
      <li>A new flood policy generally does not take effect for 30 days. That is why this
        decision has to be made on a dry day.</li>
      <li>Water backing up through a drain is usually not covered by either one. It needs its own
        endorsement, and it is the most common uncovered basement loss.</li>
    </ol>
    <h2>What it is not</h2>
    <p>Not insurance advice, not a coverage determination, not run by any insurer or agency. It
      explains what policy types generally cover and tells you which words to look for on your own
      declarations page. Only your insurer can tell you what you actually have.</p>
    <h2>Where the facts come from</h2>
    <p>Every statement about coverage or safety is cited on the page where it appears, with the
      date it was checked. See <code>SOURCES.md</code> in the repository.</p>
    ${data.local.configured ? '' : `
      <div class="callout callout-warn">
        <p><strong>Nothing local has been checked for this copy.</strong> Sandbag sites, sewer
        backup reimbursement programs, and floodplain contacts are all municipal and nobody has
        called. See <code>VERIFY.md</code>.</p>
      </div>`}`;
}

// ------------------------------------------------------------------ routing

async function route(): Promise<void> {
  const app = document.getElementById('app');
  if (!app) return;
  const section = (location.hash.replace(/^#\//, '') || 'coverage').split('/')[0];

  if (section === 'now') { app.innerHTML = renderNow(); document.title = 'Water now'; }
  else if (section === 'prepare') { app.innerHTML = renderPrepare(); document.title = 'Before it happens'; }
  else if (section === 'log') { app.innerHTML = await renderLog(); document.title = 'Damage record'; wireLog(); }
  else if (section === 'about') { app.innerHTML = renderAbout(); document.title = 'About'; }
  else { app.innerHTML = renderCoverage(); document.title = 'Am I covered?'; wireCoverage(); }

  document.getElementById('main')?.focus();
}

function wireCoverage(): void {
  const app = document.getElementById('app')!;
  app.addEventListener('change', (ev) => {
    const t = ev.target as HTMLInputElement;
    const a = readAnswers();
    if (t.name === 'tenure') a.tenure = t.value as 'own' | 'rent';
    else if (t.name?.startsWith('gap-')) a.gaps[t.name.slice(4)] = t.value as GapState;
    else if (t.name === 'exc') {
      a.exceptions = t.checked
        ? [...new Set([...a.exceptions, t.value])]
        : a.exceptions.filter((x) => x !== t.value);
    } else return;
    writeAnswers(a);
    const open = app.querySelector('details')?.open;
    app.innerHTML = renderCoverage();
    if (open) app.querySelector('details')?.setAttribute('open', '');
    wireCoverage();
  });
}

async function addTypedEntry(kind: 'damage' | 'call' | 'receipt'): Promise<void> {
  const val = (id: string) => (document.getElementById(id) as HTMLInputElement | HTMLSelectElement)?.value.trim() ?? '';
  let body: Record<string, unknown>;

  if (kind === 'damage') {
    if (!val('d-desc')) return alert('Say what the item is first.');
    const cost = val('d-cost') ? parseMoneyToCents(val('d-cost')) : null;
    if (val('d-cost') && cost === null) return alert("Couldn't read that amount. Try something like 900 or 899.99.");
    const year = val('d-year') ? Number(val('d-year')) : null;
    body = {
      kind: 'damage', room: val('d-room') || 'Not said', description: val('d-desc'),
      purchaseCostCents: cost, purchaseYear: Number.isFinite(year) && year ? year : null,
      condition: val('d-cond') || 'unknown',
    };
  } else if (kind === 'call') {
    if (!val('c-party') && !val('c-summary')) return alert('Say who you called, or what was said.');
    body = {
      kind: 'call', party: val('c-party') || 'Not said', person: val('c-person'),
      summary: val('c-summary'),
      ...(val('c-claim') ? { claimNumber: val('c-claim') } : {}),
      ...(val('c-promised') ? { promised: val('c-promised') } : {}),
    };
  } else {
    const amount = parseMoneyToCents(val('r-amount'));
    if (amount === null) return alert("Couldn't read that amount. Try something like 89.99.");
    if (!val('r-vendor')) return alert('Say who you paid.');
    body = {
      kind: 'receipt', vendor: val('r-vendor'), amountCents: amount,
      category: val('r-cat') || 'other',
      datedOn: val('r-date') || new Date().toISOString().slice(0, 10),
    };
  }

  chain = [...chain, await appendEntry(chain, body, new Date().toISOString())];
  try {
    await saveChain(chain);
  } catch (err) {
    if (!(err instanceof StorageUnavailableError)) throw err;
    unsavedCount++;
    alert(
      'This device would not save the record — it may be out of space, or this may be a private ' +
        'window. The entry is still here for now. Save the PDF before you close this tab.',
    );
  }
  await route();
}

function wireLog(): void {
  document.getElementById('add')?.addEventListener('click', () => { void addLogEntry(); });
  document.querySelectorAll('[data-add]').forEach((btn) => {
    btn.addEventListener('click', () => {
      void addTypedEntry((btn as HTMLElement).dataset.add as 'damage' | 'call' | 'receipt');
    });
  });
  document.getElementById('export-zip')?.addEventListener('click', () => {
    void (async () => {
      const [{ buildOriginalsZip, downloadZip }, { verifyChain }, { getBlob }] = await Promise.all([
        import('./export.js'), import('./evidence.js'), import('./store.js'),
      ]);
      const on = new Date().toISOString().slice(0, 10);
      const { zip, missing } = await buildOriginalsZip(chain, getBlob, await verifyChain(chain), on);
      if (missing.length) {
        alert(
          `${missing.length} photo file(s) are recorded but no longer on this device. The ` +
            'manifest lists them so the gap is visible rather than silent.',
        );
      }
      downloadZip(zip, `water-damage-originals-${on}.zip`);
    })();
  });

  document.getElementById('export')?.addEventListener('click', () => {
    void (async () => {
      // Loaded on demand. pdf-lib is ~175KB gzipped and the emergency screen must not carry it:
      // that screen has to render offline in under two seconds on a bad phone, and nobody
      // reaching it is about to generate a PDF. The byte-budget check caught this as a
      // regression after the export landed — same treatment as exifr.
      const { buildPacket, downloadBlob } = await import('./export.js');
      const bytes = await buildPacket(chain, new Date().toISOString().slice(0, 10));
      downloadBlob(bytes, `water-damage-record-${new Date().toISOString().slice(0, 10)}.pdf`);
    })();
  });
}

const buildLine = document.getElementById('build-line');
if (buildLine) buildLine.textContent = `Data built ${data.builtAt}`;

window.addEventListener('hashchange', () => { void route(); });
void route();

// Offline is not a nicety here. The power is out during the event this app exists for, and the
// emergency screen is the reason it exists. Registration failure never blocks the page.
if ('serviceWorker' in navigator && location.protocol !== 'file:') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch(() => {});
  });
}
