import indexData from './generated/index.json';
import type { DataIndex, I18nText, Item, Location, ResolvedAnswer } from './types.js';
import { SearchIndex } from './search.js';
import { isDisambiguation, resolve, VERDICT_LABEL, VERDICT_SUBTEXT } from './resolve.js';
import { logZeroResult } from './telemetry.js';
import {
  queue, questions, isStale, daysSince, readVerifications, recordVerification, toYaml,
  type Outcome,
} from './verify.js';

const data = indexData as unknown as DataIndex;
const lang = pickLang();
const search = new SearchIndex(data.items, data.jurisdiction.languages);
const bySlug = new Map(data.items.map((i) => [i.slug, i]));

function pickLang(): string {
  const supported = data.jurisdiction.languages;
  for (const want of navigator.languages ?? [navigator.language]) {
    const base = (want ?? 'en').split('-')[0];
    if (supported.includes(base)) return base;
  }
  return 'en';
}

/** Falls back to English rather than rendering nothing. A missing translation must never
 *  produce a blank instruction on a page about propane cylinders. */
function t(text: I18nText | undefined): string {
  if (!text) return '';
  return text[lang] ?? text.en;
}

/** Aliases are stored lowercase so search normalization is trivial; headings want a capital. */
function displayName(item: Item): string {
  const raw = item.names[lang]?.[0] ?? item.names.en[0];
  return raw.charAt(0).toUpperCase() + raw.slice(1);
}

/**
 * An unfilled placeholder must never appear in a sentence aimed at a user. A bracketed value
 * means setup was skipped, and "call [HAULER]" reads as a bug rather than an instruction.
 */
function haulerName(): string {
  const h = data.jurisdiction.hauler;
  return !h || h.startsWith('[') ? 'your trash company' : h;
}

function esc(s: string): string {
  return s.replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!,
  );
}

const HAZARD_WORD: Record<string, string> = {
  none: '',
  caution: 'Handle with care',
  hazardous: 'Hazardous',
  professional: 'Do not handle yourself',
};

// ------------------------------------------------------------------ rendering

function renderHome(query = ''): string {
  return `
    <h1>What do I do with this?</h1>
    <form role="search" onsubmit="return false">
      <label class="search-label" for="q">Type the thing you're trying to get rid of</label>
      <p class="search-hint" id="q-hint">
        Plain words are fine — "weed killer", "the swirly light bulbs", "swollen laptop battery".
      </p>
      <input
        type="search" id="q" name="q" autocomplete="off" autocapitalize="off"
        spellcheck="false" aria-describedby="q-hint" value="${esc(query)}"
        placeholder="batteries, paint, medicine…" />
    </form>
    <div id="results" aria-live="polite"></div>
    ${configBanner()}
  `;
}

function configBanner(): string {
  if (data.jurisdiction.configured) return '';
  return `
    <div class="callout callout-warn" style="margin-top:2rem">
      <p><strong>This copy isn't set up for a real town yet.</strong></p>
      <p>
        It can tell you what something is and why it's dangerous — that part is the same
        everywhere. It can't tell you which of your bins it goes in, because nobody has called
        the county and asked. Those answers are municipal and this app refuses to guess them.
      </p>
      <p class="no-print">Setting it up is a morning of phone calls. See <code>VERIFY.md</code>.</p>
    </div>`;
}

function renderResults(query: string): string {
  const hits = search.search(query);
  if (!query.trim()) return '';
  if (hits.length === 0) {
    logZeroResult(query, lang);
    return `
      <div class="no-results">
        <p><strong>No match for "${esc(query)}".</strong></p>
        <p>
          Try another word for it. If nothing works, that's a gap in this list, not in you —
          call your county's solid waste office and ask, and the safest answer in the meantime
          is household hazardous waste, which is never wrong.
        </p>
      </div>`;
  }
  return `
    <ul class="results">
      ${hits
        .map((h) => {
          const name = displayName(h.item);
          const via =
            h.matched.toLowerCase() !== name.toLowerCase()
              ? `<span class="result-via">matched "${esc(h.matched)}"</span>`
              : '';
          return `<li><a href="#/item/${h.item.slug}">
              <span class="result-name">${esc(name)}</span> ${via}
            </a></li>`;
        })
        .join('')}
    </ul>`;
}

function renderDisambiguation(item: Item): string {
  const name = displayName(item);
  const kids = (item.disambiguates ?? []).map((s) => bySlug.get(s)).filter((i): i is Item => !!i);
  return `
    <p><a href="#/">&larr; Search again</a></p>
    <h1>Which kind of ${esc(name)}?</h1>
    <div class="callout callout-warn">
      <p>
        These have different answers, and one of them starts fires in garbage trucks. Pick the
        one you're holding.
      </p>
    </div>
    <ul class="results">
      ${kids
        .map((k) => {
          const kn = displayName(k);
          const ex = (k.names[lang] ?? k.names.en).slice(1, 4).join(', ');
          return `<li><a href="#/item/${k.slug}">
            <span class="result-name">${esc(kn)}</span>
            ${ex ? `<span class="result-via">${esc(ex)}</span>` : ''}
          </a></li>`;
        })
        .join('')}
    </ul>`;
}

function hoursLine(loc: Location): string {
  if (loc.hoursNote) return esc(t(loc.hoursNote));
  if (!loc.hours) return 'Hours not recorded — call first.';
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const parts: string[] = [];
  for (let d = 0; d < 7; d++) {
    const spans = (loc.hours as Record<number, { open: string; close: string }[]>)[d];
    if (spans?.length) parts.push(`${days[d]} ${spans.map((s) => `${s.open}–${s.close}`).join(', ')}`);
  }
  return parts.length ? esc(parts.join(' · ')) : 'Hours not recorded — call first.';
}

function renderPlace(loc: Location): string {
  return `
    <div class="place">
      <p class="place-name">${esc(loc.name)}</p>
      <p class="place-meta">${esc(loc.address)}</p>
      ${loc.phone ? `<p class="place-meta"><a href="tel:${esc(loc.phone)}">${esc(loc.phone)}</a></p>` : ''}
      <p class="place-meta">${hoursLine(loc)}</p>
      ${loc.proofRequired ? `<p class="place-meta">Bring: ${esc(t(loc.proofRequired))}</p>` : ''}
      ${loc.feesNote ? `<p class="place-meta">${esc(t(loc.feesNote))}</p>` : ''}
      <p class="place-meta">${
        loc.verifiedOn
          ? `Confirmed ${esc(loc.verifiedOn)} by ${esc(loc.verifiedBy ?? 'unknown')}`
          : 'Not confirmed — call first.'
      }</p>
    </div>`;
}

function verdictClass(a: ResolvedAnswer): string {
  if (a.hazard === 'hazardous' || a.hazard === 'professional') return 'verdict verdict-danger';
  if (!a.isLocal) return 'verdict verdict-warn';
  return 'verdict';
}

function renderAnswer(item: Item): string {
  const a = resolve(data, item);
  const name = displayName(item);
  const hazardWord = HAZARD_WORD[a.hazard];

  const caveat =
    a.caveat === 'not_configured' || a.caveat === 'no_data'
      ? `<div class="callout callout-warn">
           <p><strong>Nobody has confirmed the rule for your area.</strong></p>
           <p>
             This app won't guess which bin. Call ${esc(haulerName())} or your
             county's solid waste office and ask about "${esc(name)}". If you'd rather not wait,
             household hazardous waste accepts things it doesn't have to — it is never the
             wrong answer, only the inconvenient one.
           </p>
         </div>`
      : a.caveat === 'demo_data'
        ? `<div class="callout callout-warn">
             <p>The only places listed for this item are demo rows, so they've been hidden.</p>
           </div>`
        : '';

  return `
    <p class="no-print"><a href="#/">&larr; Search again</a></p>
    <h1>${esc(name)}</h1>

    <div class="${verdictClass(a)}">
      ${hazardWord ? `<span class="hazard-tag">${esc(hazardWord)}</span>` : ''}
      <p class="verdict-word">${esc(VERDICT_LABEL[a.verdict])}</p>
      <p class="verdict-sub">${esc(VERDICT_SUBTEXT[a.verdict])}</p>
    </div>

    ${a.why ? `<h2>Why</h2><p>${esc(t(a.why))}</p>` : ''}

    ${
      a.prep.length
        ? `<h2>Before you go</h2><ul class="prep">${a.prep.map((p) => `<li>${esc(t(p))}</li>`).join('')}</ul>`
        : ''
    }

    ${caveat}

    ${
      a.destinations.length
        ? `<h2>Where to take it</h2>${a.destinations.map(renderPlace).join('')}`
        : ''
    }

    ${
      a.nationalOptions.length
        ? `<h2>Works anywhere</h2><ul class="plain">${a.nationalOptions
            .map((o) => `<li>${linkify(esc(t(o)))}</li>`)
            .join('')}</ul>`
        : ''
    }

    ${
      a.sources.length
        ? `<h2>Where this came from</h2>
           <ul class="plain sources">${a.sources
             .map(
               (s) =>
                 `<li>${esc(s.org)}, <a href="${esc(s.url)}" rel="noopener">${esc(s.title)}</a> —
                  checked ${esc(s.retrieved)}${s.method === 'search_index' ? ' (via search index, not fetched)' : ''}</li>`,
             )
             .join('')}</ul>`
        : ''
    }

    <p class="meta-line">
      ${a.verifiedOn ? `Local rule confirmed ${esc(a.verifiedOn)} by ${esc(a.verifiedBy ?? '')}. ` : ''}
      Data built ${esc(data.builtAt)}.
    </p>

    <p class="no-print">
      <button class="link" id="report" data-slug="${esc(item.slug)}">
        This is wrong, or they were closed
      </button>
    </p>`;
}

/** Turns bare URLs in content into links. Content is escaped before this runs. */
function linkify(escaped: string): string {
  return escaped.replace(/https?:\/\/[^\s<]+/g, (u) => `<a href="${u}" rel="noopener">${u}</a>`);
}

function renderList(): string {
  const rows = [...data.items]
    .filter((i) => !isDisambiguation(i))
    .sort((a, b) => a.category.localeCompare(b.category) || a.slug.localeCompare(b.slug))
    .map((i) => {
      const a = resolve(data, i);
      return `<tr>
        <td>${esc(displayName(i))}</td>
        <td>${esc(i.category)}</td>
        <td>${esc(VERDICT_LABEL[a.verdict])}</td>
      </tr>`;
    })
    .join('');
  return `
    <p class="no-print"><a href="#/">&larr; Search</a></p>
    <h1>Everything on this list</h1>
    <p>Printable. Put it on a fridge or a bulletin board.</p>
    <table class="list">
      <thead><tr><th>Item</th><th>Category</th><th>Answer</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    ${configBanner()}`;
}

function renderVerify(): string {
  const today = new Date();
  const done = new Set(readVerifications().map((r) => r.locationId));
  const pending = queue(data, today, done);
  const loc = pending[0];
  const records = readVerifications();

  const exportBlock = records.length
    ? `<h2>What you've checked</h2>
       <p>${records.length} location${records.length === 1 ? '' : 's'} this session.</p>
       <pre class="sources" style="white-space:pre-wrap;border:1px solid var(--line);padding:.75rem;border-radius:var(--radius)">${esc(toYaml(records, data))}</pre>
       <p><button class="btn btn-secondary" id="clear-verifications">Start over</button></p>`
    : '';

  if (!loc) {
    return `
      <p class="no-print"><a href="#/">&larr; Search</a></p>
      <h1>Re-check the list</h1>
      <div class="callout callout-warn"><p><strong>Nothing left in the queue.</strong>
        ${data.locations.length === 0 ? 'There are no locations at all yet — see VERIFY.md.' : ''}</p></div>
      ${exportBlock}`;
  }

  const days = daysSince(loc.verifiedOn, today);
  const age = days === null
    ? 'never confirmed'
    : `last confirmed ${days} day${days === 1 ? '' : 's'} ago`;

  return `
    <p class="no-print"><a href="#/">&larr; Search</a></p>
    <h1>Re-check the list <span class="result-via">(${pending.length} to go)</span></h1>
    <p>One call, about a minute of their time. The questions are below — you only have to type
      something if an answer changed.</p>

    ${loc.isDemo ? `<div class="callout callout-danger"><p><strong>This is a demo row, not a real
      place.</strong> Delete <code>data/locations/demo.yaml</code> and add places you have
      actually called. See <code>VERIFY.md</code>.</p></div>` : ''}

    <div class="place">
      <p class="place-name">${esc(loc.name)}</p>
      <p class="place-meta">${esc(loc.address)}</p>
      ${loc.phone ? `<p><a class="btn" href="tel:${esc(loc.phone)}">Call ${esc(loc.phone)}</a></p>`
        : '<p class="place-meta">No phone number recorded — find one first.</p>'}
      <p class="place-meta">${esc(age)}${isStale(loc, today) ? ' — due' : ''}
        ${loc.verifiedBy ? `· last by ${esc(loc.verifiedBy)}` : ''}</p>
    </div>

    <h2>Ask</h2>
    <ol class="plain">${questions(loc, data).map((q) => `<li>${esc(q)}</li>`).join('')}</ol>

    <h2>What happened</h2>
    <p><label for="who"><strong>Your name</strong> (goes in the record as who confirmed it)</label>
      <input type="text" id="who" value="${esc(localStorage.getItem('dg.verifier') ?? '')}" /></p>
    <p><label for="vnote"><strong>Anything that changed</strong> (only if it did)</label>
      <input type="text" id="vnote" placeholder="Now closed Saturdays; $5 per load" /></p>
    <p>
      <button class="btn" data-outcome="confirmed">Still correct</button>
      <button class="btn btn-secondary" data-outcome="changed">Something changed</button>
      <button class="btn btn-secondary" data-outcome="closed">They've closed</button>
      <button class="btn btn-secondary" data-outcome="no_answer">No answer</button>
    </p>
    <p class="place-meta">"No answer" is recorded as an attempt and does not update the date —
      a location nobody can reach is a finding, not a confirmation.</p>

    ${exportBlock}`;
}

function renderAbout(): string {
  return `
    <p class="no-print"><a href="#/">&larr; Search</a></p>
    <h1>About this</h1>
    <p>
      A volunteer-run lookup for how to get rid of things where you live. It is not run by
      ${esc(data.jurisdiction.city)}, the county, or ${esc(haulerName())}.
    </p>
    <h2>How it decides what to tell you</h2>
    <p>
      Two kinds of fact go into every answer. The first is true everywhere — a lithium battery
      starts fires when it is crushed, a needle can stick a sanitation worker. Those come from
      federal agencies and every one of them is cited at the bottom of the answer.
    </p>
    <p>
      The second is which of <em>your</em> bins something goes in. That is municipal, it changes,
      and it is only true after somebody phones and confirms it. When nobody has, this app says
      so instead of guessing.
    </p>
    <h2>When it doesn't know</h2>
    <p>
      The answer is household hazardous waste and a phone number. That is never the wrong answer,
      only the inconvenient one — and it is a great deal better than telling you to put a propane
      cylinder in a truck.
    </p>
    <h2>Found something wrong?</h2>
    <p>
      Use the "this is wrong" button on any answer. A report from someone who stood at the door
      is the most useful thing this project receives.
    </p>`;
}

// ------------------------------------------------------------------ routing

function route(): void {
  const app = document.getElementById('app');
  if (!app) return;
  const hash = location.hash.replace(/^#/, '') || '/';
  const [, section, arg] = hash.split('/');

  if (section === 'item' && arg) {
    const item = bySlug.get(arg);
    if (item) {
      app.innerHTML = isDisambiguation(item) ? renderDisambiguation(item) : renderAnswer(item);
      document.title = `${displayName(item)} — What do I do with this?`;
      wireAnswer();
      focusMain();
      return;
    }
  }
  if (section === 'list') {
    app.innerHTML = renderList();
    document.title = 'All items — What do I do with this?';
    focusMain();
    return;
  }
  if (section === 'verify') {
    app.innerHTML = renderVerify();
    document.title = 'Re-check the list';
    wireVerify();
    focusMain();
    return;
  }
  if (section === 'about') {
    app.innerHTML = renderAbout();
    document.title = 'About — What do I do with this?';
    focusMain();
    return;
  }

  app.innerHTML = renderHome();
  document.title = 'What do I do with this?';
  wireSearch();
}

/** Moves focus so a screen reader announces the new screen after client-side navigation. */
function focusMain(): void {
  document.getElementById('main')?.focus();
}

function wireSearch(): void {
  const input = document.getElementById('q') as HTMLInputElement | null;
  const out = document.getElementById('results');
  if (!input || !out) return;

  let timer: ReturnType<typeof setTimeout> | undefined;
  const run = () => {
    out.innerHTML = renderResults(input.value);
  };
  input.addEventListener('input', () => {
    clearTimeout(timer);
    // Short debounce: long enough to avoid logging every keystroke as a zero-result,
    // short enough that the answer feels instant.
    timer = setTimeout(run, 140);
  });
  input.focus();
}

function wireVerify(): void {
  const app = document.getElementById('app')!;
  app.querySelectorAll('[data-outcome]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const outcome = (btn as HTMLElement).dataset.outcome as Outcome;
      const who = (document.getElementById('who') as HTMLInputElement)?.value.trim();
      const note = (document.getElementById('vnote') as HTMLInputElement)?.value.trim();
      if (!who) {
        alert('Put your name in first — the record has to say who confirmed it.');
        return;
      }
      try { localStorage.setItem('dg.verifier', who); } catch { /* not important enough to fail */ }

      const today = new Date();
      const loc = queue(data, today, new Set(readVerifications().map((r) => r.locationId)))[0];
      if (!loc) return;

      const saved = recordVerification({
        locationId: loc.id, outcome, on: today.toISOString().slice(0, 10), by: who,
        ...(note ? { note } : {}),
      });
      if (!saved) {
        alert("This device wouldn't save that. Copy the YAML below before you go any further.");
        return;
      }
      app.innerHTML = renderVerify();
      wireVerify();
    });
  });

  document.getElementById('clear-verifications')?.addEventListener('click', () => {
    if (!confirm('Clear everything you checked this session? Copy the YAML first.')) return;
    try { localStorage.removeItem('dg.verifications'); } catch { /* ignore */ }
    app.innerHTML = renderVerify();
    wireVerify();
  });
}

function wireAnswer(): void {
  const btn = document.getElementById('report');
  btn?.addEventListener('click', () => {
    const slug = (btn as HTMLElement).dataset.slug ?? '';
    const note = window.prompt(
      'What was wrong? (For example: they were closed, or they said they do not take it.)',
    );
    if (!note) return;
    const key = 'dg.reports';
    try {
      const existing = JSON.parse(localStorage.getItem(key) ?? '[]');
      existing.push({ slug, note, on: new Date().toISOString().slice(0, 10) });
      localStorage.setItem(key, JSON.stringify(existing));
    } catch {
      // Full device, or a private window. Tell them rather than appearing to have saved it.
      alert(
        "This device wouldn't save the report. Please tell whoever maintains this list directly " +
          '— see the About page.',
      );
      return;
    }
    btn.replaceWith(
      Object.assign(document.createElement('p'), {
        textContent:
          'Saved on this device. Send it to whoever maintains this list — see the About page.',
      }),
    );
  });
}

const buildLine = document.getElementById('build-line');
if (buildLine) {
  buildLine.textContent = `${data.items.length} items · data built ${data.builtAt}`;
}

window.addEventListener('hashchange', route);
route();

if ('serviceWorker' in navigator && location.protocol !== 'file:') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch(() => {
      /* offline support is an enhancement; never block the page on it */
    });
  });
}
