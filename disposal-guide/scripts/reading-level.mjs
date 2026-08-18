#!/usr/bin/env node
/**
 * Measures the reading level of every user-facing string, because the kit's ground rules promise
 * "~6th grade reading level" in all three projects and nothing has ever checked it.
 *
 * Flesch–Kincaid grade level:  0.39·(words/sentence) + 11.8·(syllables/word) − 15.59
 *
 * WHAT THIS IS NOT. Flesch–Kincaid is a rough proxy built from sentence and syllable length. It
 * cannot tell that "hazardous" is a harder word than "dangerous", it penalises correct technical
 * terms it would be wrong to remove ("lithium-ion", "municipality"), and it rewards chopping
 * sentences into fragments, which is not the same as being clearer. A high score here is a
 * question to answer, not a defect to fix by thesaurus.
 *
 * So the output is a ranked list for a human to read, and the failure threshold is set well above
 * the target: it fails on prose nobody could defend, not on prose that is merely above 6.
 *
 * Usage: node tools/reading-level.mjs <project-dir> [--max N] [--top N]
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const dir = process.argv[2] ?? new URL("..", import.meta.url).pathname;

const arg = (name, dflt) => {
  const i = process.argv.indexOf(name);
  return i > 0 ? Number(process.argv[i + 1]) : dflt;
};
const MAX_GRADE = arg('--max', 12);
const TOP = arg('--top', 12);

/**
 * The gate is on sentence LENGTH, not on the grade score.
 *
 * This matters and was changed after reading the first run's output. Flesch-Kincaid blends
 * sentence length with syllables per word, and only the first half is something a writer should
 * act on here. "Tape over the terminals with non-conductive tape, or bag each battery separately"
 * scores 12.7 — a clear twelve-word safety instruction, penalised entirely for the syllables in
 * "non-conductive" and "separately", and any rewrite to satisfy the number would be worse. So the
 * grade is reported for a human to read and argue with, and the build only fails on a sentence
 * long enough that nobody would defend it.
 */
const MAX_SENTENCE_WORDS = arg('--max-sentence', 25);

/** Syllable estimate. Wrong on plenty of words; consistent, which is what a proxy needs. */
function syllables(word) {
  const w = word.toLowerCase().replace(/[^a-z]/g, '');
  if (!w) return 0;
  if (w.length <= 3) return 1;
  const groups = w
    .replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, '')
    .replace(/^y/, '')
    .match(/[aeiouy]{1,2}/g);
  return Math.max(1, groups ? groups.length : 1);
}

export function grade(text) {
  const clean = String(text).replace(/\s+/g, ' ').trim();
  if (!clean) return null;
  const sentences = clean.split(/[.!?]+(?:\s|$)/).filter((s) => s.trim().length > 1);
  const words = clean.match(/[A-Za-z][A-Za-z'-]*/g) ?? [];
  if (words.length < 6) return null;   // too short to score meaningfully
  const nSent = Math.max(1, sentences.length);
  const nSyl = words.reduce((n, w) => n + syllables(w), 0);
  return {
    grade: 0.39 * (words.length / nSent) + 11.8 * (nSyl / words.length) - 15.59,
    words: words.length,
    sentences: nSent,
    longest: Math.max(...(sentences.length ? sentences : [clean]).map((s) => (s.match(/[A-Za-z][A-Za-z'-]*/g) ?? []).length)),
  };
}

/** Walk the built index, collecting every string a user could read, with its path. */
function collect(node, path, out) {
  if (typeof node === 'string') { out.push({ path, text: node }); return; }
  if (Array.isArray(node)) { node.forEach((v, i) => collect(v, `${path}[${i}]`, out)); return; }
  if (node && typeof node === 'object') {
    for (const [k, v] of Object.entries(node)) {
      // Identifiers, URLs and machine fields are not prose.
      if (/^(id|slug|url|href|sha256|contentHash|retrieved|method|verifiedOn|kind|hazard|severity|source|sourceRef|announcedOn|builtAt|phone|address|hours)$/.test(k)) continue;
      // Flesch-Kincaid is calibrated on English. Spanish averages more syllables per word, so
      // scoring it with this formula reports a hard read for ordinary prose and would push a
      // translator toward worse Spanish. Anything but `en` is skipped rather than mismeasured.
      if (/^(es|fr|zh|vi|ar|tl|ko|ru|pt)$/.test(k)) continue;
      // Citation titles are the publisher's words, not ours, and must not be rewritten.
      if (k === 'title' && /(^|\.)sources\[/.test(path)) continue;
      collect(v, path ? `${path}.${k}` : k, out);
    }
  }
}

const index = JSON.parse(readFileSync(join(dir, 'src', 'generated', 'index.json'), 'utf8'));
const strings = [];
collect(index, '', strings);

const scored = strings
  .map((s) => ({ ...s, ...(grade(s.text) ?? {}) }))
  .filter((s) => typeof s.grade === 'number')
  .sort((a, b) => b.grade - a.grade);

if (!scored.length) { console.log('no scorable strings found'); process.exit(0); }

const median = scored[Math.floor(scored.length / 2)].grade;
const mean = scored.reduce((n, s) => n + s.grade, 0) / scored.length;
const over = scored.filter((s) => s.grade > MAX_GRADE);

console.log(`\n  ${dir} — ${scored.length} scorable strings`);
console.log(`  median grade ${median.toFixed(1)} · mean ${mean.toFixed(1)} · target ~6\n`);
console.log(`  Hardest ${Math.min(TOP, scored.length)}:`);
for (const s of scored.slice(0, TOP)) {
  const flag = s.grade > MAX_GRADE ? '!' : ' ';
  console.log(`  ${flag} ${s.grade.toFixed(1).padStart(5)}  ${s.path}`);
  console.log(`         ${s.text.replace(/\s+/g, ' ').slice(0, 96)}${s.text.length > 96 ? '…' : ''}`);
  console.log(`         ${s.words} words, ${s.sentences} sentence(s), longest ${s.longest} words`);
}

if (over.length) {
  console.log(`\n  ${over.length} string(s) score above grade ${MAX_GRADE}. Advisory only — read them,`);
  console.log('  and shorten the sentence before reaching for a shorter word.');
}

const tooLong = scored.filter((s) => s.longest > MAX_SENTENCE_WORDS).sort((a, b) => b.longest - a.longest);
if (tooLong.length) {
  console.log(`\n  FAIL: ${tooLong.length} sentence(s) longer than ${MAX_SENTENCE_WORDS} words:\n`);
  for (const s of tooLong) {
    console.log(`    ${String(s.longest).padStart(3)} words  ${s.path}`);
    console.log(`             ${s.text.replace(/\s+/g, ' ').slice(0, 100)}`);
  }
  console.log('');
  process.exit(1);
}
console.log(`\n  no sentence longer than ${MAX_SENTENCE_WORDS} words\n`);
