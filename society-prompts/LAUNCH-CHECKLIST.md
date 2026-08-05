# Launch Checklist

Before a real person relies on any of this. Not a formality — several of these projects touch
benefits, medical bills, housing, and disaster response, where confidently wrong output does
measurable damage.

Work top to bottom. The first section is the one that decides whether you launch at all.

---

## 1. The harm question

Answer in writing, in your README, before anything else.

- [ ] **When this is wrong, who gets hurt and how badly?** Write the worst realistic case in
      one paragraph. Not the worst imaginable — the worst likely.
- [ ] **Which direction of error is worse?** Almost always one is. A benefits screener that
      says "you don't qualify" when you do costs someone a year of food assistance; the
      opposite costs a wasted afternoon. Decide which way your uncertainty resolves, encode it,
      and write it in a code comment where the decision lives.
- [ ] **What does the tool do when it doesn't know?** "Unknown," "call first," and "we're not
      sure" must be first-class outputs, as easy to reach as a confident answer.
- [ ] **Is there a human backstop, and is their number on every page?** For anything touching
      health, money, housing, or safety, there must be one. A tool that hands someone a
      question and no one to ask has moved the problem, not solved it.
- [ ] **Have you drawn the professional line explicitly?** Not legal advice, not medical
      advice, not an eligibility determination, not an emergency service. Stated in the app, in
      plain words, where the user will actually see it — not buried in a footer.

If you can't answer these, don't launch. Fix the design.

---

## 2. Truth and sourcing

- [ ] Every number displayed to a user traces to a primary source, with the URL and the date it
      was retrieved recorded in the repo.
- [ ] Every statistic in the UI has a year and a named source, or has been deleted. Unsourced
      statistics get deleted — no exceptions, no "roughly."
- [ ] Every rule, threshold, income limit, statutory citation, and code set is dated, and the
      app shows its age when displaying it.
- [ ] Anything past its refresh window renders a visible staleness warning to the user, not
      just a log line.
- [ ] `MAINTENANCE.md` exists and says what needs updating, from where, and in which month.
- [ ] You have a written list of everything you could not verify, and none of it is being
      presented to users as fact.

---

## 3. Privacy

- [ ] You have called every public endpoint unauthenticated and read the raw bytes. No
      addresses, phone numbers, precise coordinates, health data, income, or immigration-related
      fields appear anywhere they shouldn't.
- [ ] Third-party requests: you have loaded the app with devtools open and listed every domain
      contacted. Each one is justified or gone. For the local-first projects, the list is empty.
- [ ] Logs contain no personal data — check application logs, access logs, and error traces.
- [ ] Sensitive fields are actually encrypted at rest; verified by reading raw storage.
- [ ] Data retention is implemented as a job that runs, not a sentence in a policy. You have
      watched it delete something.
- [ ] Users are told, in plain language and before they enter anything, what is stored and
      where. If the answer is "nothing leaves your device," that claim is architecturally true
      and a user can verify it in devtools.
- [ ] There is a way to be deleted, and you have tested it.

---

## 4. It works for the person it's for

- [ ] axe-core clean on every page, in CI.
- [ ] You have completed the full critical path with keyboard only, and with a screen reader.
- [ ] Usable at 200% zoom on a 360px viewport with no horizontal page scrolling.
- [ ] Reading level checked and at target. Error messages included — check those specifically.
- [ ] Every translated string exists; nothing silently falls back to English. A human who
      speaks the language has read the translation, especially for anything with legal or
      medical terminology.
- [ ] Loaded and used on a genuinely old, cheap phone over a throttled connection. You have the
      measured load time written down.
- [ ] Works, or degrades honestly, with JavaScript disabled — for any project where that was a
      stated constraint.
- [ ] Printed pages print correctly on standard paper.

---

## 5. It survives contact with reality

- [ ] Every external data source has been failure-tested: 500, timeout, empty, malformed,
      rate-limited. The app degrades visibly and never substitutes a silent default.
- [ ] Scheduled jobs are persisted and idempotent. You have killed the process mid-run and
      confirmed correct resumption.
- [ ] Concurrency is decided by database constraints, not application logic. You have run the
      concurrent test.
- [ ] Timezone and DST correctness tested with the server in UTC and users elsewhere, in both
      transition directions.
- [ ] Rate limiting exists on anything that sends a message or costs money, with a hard daily
      ceiling and an alert.
- [ ] A backup exists and you have restored from it into a scratch environment.
- [ ] A fresh clone plus the README gets a stranger to a running app. You have tested this by
      following your own README literally.

---

## 6. The human infrastructure

This is the part software people skip and it is usually why these projects die.

- [ ] **You have talked to the org that already does this work.** Not emailed — talked. They
      know things that will change your design, and if they aren't involved, your tool competes
      with them for the same users' trust.
- [ ] **Someone other than you has used it, while you watched silently.** Not a demo you drove.
      Count where they hesitated. That's your bug list.
- [ ] **A domain expert has reviewed the output.** A caseworker for the benefits screener, a
      legal aid attorney for the tenant letters, a patient advocate for the bill letters, a
      pharmacist for the prescription scripts, a wheelchair user for the accessibility viewer,
      a worker center organizer for the wage claim packet, a court clerk or public defender for
      the court procedure pages, a civil rights advocate for the language access claims. This
      gate appears in every prompt in this kit and it is the one most worth honoring.
- [ ] **You know who maintains this in a year.** If it's you, look at `MAINTENANCE.md` and
      decide honestly whether you'll do it. If the answer is no, either find a home for it or
      build the version that fails safe when abandoned.
- [ ] **The README says what happens if you disappear**: what this is, who it serves, who to
      contact, what to do first.

---

## 7. The lines not to cross

Applies to everything in this kit.

- [ ] No monetization of a vulnerable user's attention. No ads, no affiliate links, no lead
      generation, no referral fees, no "sponsored" placements. If you find yourself designing a
      funnel, stop — that is the mechanism by which every commercially-run version of these
      tools became untrustworthy.
- [ ] No dark patterns. No fake urgency, no manufactured scarcity, no obstacles to leaving, no
      pre-checked consent.
- [ ] No collection "because it might be useful later." Collect what the feature needs today.
- [ ] No presenting yourself as official when you're not. Say plainly that you're an
      independent or volunteer project, and link the official source.
- [ ] No LLM output presented to a user as fact without a human review step and a source
      citation. In the eligibility, pricing, legal, and medical paths in this kit, no LLM at
      request time at all.
- [ ] No public database of individuals — not bad landlords, not people who need help, not
      businesses graded on compliance. Every one of these turns a helpful tool into a weapon
      and ends the project.
- [ ] No feature that makes it easier for someone to be targeted: no public map of vulnerable
      people, no addresses attached to health or income, no searchable index of names pulled
      from public records.

---

## 8. Launch small

- [ ] Launch to a number of people you can personally support. Five is a fine number.
- [ ] Have a way to hear that it broke — a phone number or an email that a human reads.
- [ ] Write down what you'll measure and what would tell you to stop. Not vanity metrics:
      for the ride tool it's failed rides, for the food tool it's completed pickups, for the
      check-in board it's how long it took to physically reach everyone unaccounted for.
- [ ] Set a date, three months out, to re-verify every external number and rule.

---

**The last check.** Read the harm paragraph you wrote in section 1. If you still believe it,
launch. If the honest answer is "I don't actually know what happens when this is wrong," you
have one more thing to do before you find out on someone else.
