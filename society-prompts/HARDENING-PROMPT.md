# The Hardening Prompt

Paste this after v1 works. It assumes the thing exists and tries to break it, in the order that
finds the worst problems first.

Do not paste it too early. Hardening a half-built feature wastes both passes. The right moment
is when the happy path runs end to end and you're tempted to show someone.

---

```text
The project in this repository works on the happy path. Your job now is to find where it fails
and fix it, in the order below. Do not add features. Do not refactor for elegance. Do not ask
me what to prioritize — the order is given.

Work through the passes in sequence. After each pass, report what you found and what you fixed,
and be specific. "Improved error handling" tells me nothing; "the SMS webhook returned 200 on a
malformed body and silently dropped the claim, fixed with explicit validation and a test"
tells me something.

Rule for the whole exercise: VERIFY BY RUNNING. A claim without an execution behind it does not
count. If something cannot be run here, say so plainly instead of implying it was checked. If a
test passes on the first try, look at it again — a green test on a bug you were sure existed
usually means the test isn't testing what you think.

=== PASS 1 — THE DATA IS PROBABLY LYING ===

Every external data source, one at a time:
1. Fetch it right now. Does it still exist? Same shape? Same field names?
2. What is its actual rate limit, and what happens when you exceed it? Trigger it deliberately.
3. What happens when it returns 500, times out, returns HTML instead of JSON, or returns an
   empty array? Test each. The app must degrade visibly, never silently substitute a default.
   A zero displayed as data is the worst outcome — worse than an error.
4. How stale can its data be, and does the UI say so? Find every number displayed without a
   date and either date it or remove it.
5. For every hardcoded threshold, rate, limit, or rule in the codebase: where did it come from?
   Produce a list with sources and retrieval dates. Anything you cannot source, flag loudly —
   that number was probably invented at some point, possibly by you.

Then check the arithmetic. Pick the three most consequential computed values in the app and
verify each by hand against a primary source. Show your work.

=== PASS 2 — PRIVACY LEAKS ===

1. Enumerate every route, endpoint, and page. For each, write down what data it returns and to
   whom. Then actually call each one unauthenticated and read the raw response bytes — not the
   rendered UI. Look for: addresses, phone numbers, exact coordinates, health information,
   income, immigration-related fields, names attached to sensitive attributes.
2. Check every response for over-fetching: an endpoint that returns a whole user row and lets
   the frontend hide fields is a leak.
3. Signed tokens and magic links: can a token for resource A be replayed against resource B?
   Do they expire? What happens on reuse? Are they in URLs that end up in logs, referrer
   headers, or a shared browser history?
4. Grep the codebase for third-party requests: fonts, analytics, error reporting, maps, CDNs.
   Load the app with devtools open and list every domain contacted. Justify each or remove it.
5. Check logs — application logs, access logs, error traces — for personal data. A stack trace
   with a phone number in it is a leak with a long retention period.
6. Check what an exported file, printed page, or generated PDF contains that the screen didn't.
7. If there's a database, verify that fields the spec said were encrypted actually are, by
   reading the raw storage.

Report every leak found and fixed. If you find none, say what you checked, because "none found"
without a method is not a finding.

=== PASS 3 — THE FAILURE PATHS ===

Run each of these for real, not as a thought experiment:
1. Network off, mid-action. Then back on. Any duplicates? Any lost writes?
2. Kill the process mid-transaction and mid-scheduled-job. Restart. What was lost? What ran
   twice? Every scheduled job must be persisted and idempotent.
3. Two concurrent conflicting actions on the same resource. Ten of them. Does a database
   constraint decide the winner, or does application code race?
4. Storage full — quota exceeded in the browser, disk full on the server. Is the failure
   visible and actionable, or silent?
5. A malformed input at every entry point: empty, enormous, wrong type, unicode, emoji, RTL
   text, a name with an apostrophe, a 400-character address, a phone number with letters.
6. Clock problems: a date near midnight, a DST transition in both directions, a server in UTC
   with users in another zone, a leap day. Run the test suite with TZ set to at least two zones
   and assert identical results.
7. Empty states: zero records, one record, and 10,000 records. Does anything break, or become
   unusable, at either end?
8. Slow: throttle to Slow 4G with 4x CPU slowdown. Use the app. Time the critical path and
   report the real number.

=== PASS 4 — ABUSE ===

Assume someone hostile finds this. Work through:
1. Can anyone enumerate records by incrementing an ID? Fix with unguessable identifiers.
2. Is there any unauthenticated action that costs money or sends a message? SMS endpoints are
   the classic: an open send endpoint gets abused for toll fraud within days. Rate limit per
   phone number, per IP, and globally, with a hard daily ceiling and an alert.
3. Can someone spam the system with fake records — fake surplus posts, fake needs, fake
   check-ins? What's the cheapest control that doesn't burden real users? Usually: a
   coordinator approval step on the thing that scales, not a CAPTCHA on everything.
4. Can a user's action harm another user? Canceling someone else's claim, revealing someone
   else's address, marking someone else safe when they aren't.
5. Injection: parameterized queries everywhere, output escaped, no template injection, no
   unsafe HTML rendering of user content, no shelling out with user input.
6. File uploads: type validated by content not extension, size limited, never served from the
   app's origin with a user-controlled content type, metadata stripped where the spec requires.
7. What does the system do if the same person floods it with a hundred requests? Answer with a
   test.

=== PASS 5 — THE PEOPLE IT WAS BUILT FOR ===

1. Run axe-core on every page. Fix every violation. Then do what axe cannot: complete the
   entire critical path with the keyboard only, then with a screen reader. Report where you
   got stuck, because that's where a real user gets stuck.
2. Set the browser to 200% zoom on a 360px-wide viewport. Is anything unreachable? Does
   horizontal scrolling appear on the page body?
3. Check color contrast on every text and UI element, including disabled states, placeholder
   text, and focus rings. Then check that no information is conveyed by color alone.
4. Run every user-facing string through a reading-level check. Report the score and rewrite
   anything above the project's target. Pay special attention to error messages — they are
   written last and are always the worst-written text in an app.
5. Check every translated string exists and is not silently falling back to English. Find any
   place where an untranslated string reaches a user.
6. Load the app on the oldest, cheapest phone you can find or emulate. Not a simulator on a
   fast laptop — a real constrained device profile. Report what breaks.
7. Print every page that is meant to be printed. Does it fit? Is anything cut off? Are links
   readable as text?

=== PASS 6 — THE HONEST INVENTORY ===

Produce these lists. This pass is the most valuable and the most likely to be skipped:

A. Every claim the app makes to a user that you have not verified against a primary source.
B. Every number in the codebase with no cited origin.
C. Every place the app could show something confidently wrong, and what the consequence would
   be for the person reading it.
D. Every dependency that, if it disappeared tomorrow, breaks the app — and what happens then.
E. Every piece of the spec that was quietly not built, or built differently than specified.
F. Every test that passes but does not actually test what its name says.
G. The three most likely reasons this project will be abandoned in six months.

Do not soften any of these lists. E and F in particular: an agent's own quiet substitutions are
exactly what a later maintainer cannot find.

=== PASS 7 — MAINTENANCE REALITY ===

1. Which data in this project goes stale, and how fast? Income limits, statute citations,
   opening hours, phone numbers, API schemas, AQI breakpoints. For each, write down the refresh
   procedure and the month it needs doing, in a MAINTENANCE.md.
2. Make staleness visible in the app, not just in a comment. Anything past its refresh window
   should say so to the user.
3. Can a person who is not you run this? Try it: fresh clone, follow the README exactly, note
   every step that fails or requires knowledge that isn't written down. Fix the README.
4. Backups: does one exist, and have you restored from it? Restore it now, into a scratch
   database, and confirm the data is intact. An untested backup is not a backup.
5. What happens if you get hit by a bus? Write the paragraph in the README that tells the next
   person what this is, who it serves, who to contact, and what to do first.

=== HOW TO REPORT ===

Per pass: what you checked, what you found, what you fixed, what you could not fix and why.

Then, at the end, one paragraph answering: if a real person relies on this tomorrow, what is
the most likely way it hurts them? Answer honestly, even if the answer is "nothing, it just
stops working" — and especially if it isn't.
```

---

## Notes

**Pass 1 first because data rot is the failure that silently invalidates everything above it.**
An accessible, fast, well-tested app displaying last year's income limits is a worse artifact
than a rough one displaying this year's, because it's trusted.

**Pass 6 is the one that gets skipped and the one worth the most.** Lists E and F — quiet
substitutions and tests that don't test what they claim — are invisible to everyone except the
agent that made them, and they only surface under a direct instruction to enumerate them.

**The closing question is deliberately blunt.** "How does this hurt someone" produces different
and better answers than "what are the risks," and for this category of project it's the right
question to end on.
