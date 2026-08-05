# 01 — Surplus Food Rescue Dispatch

**What it is:** A pager for perishable food. A bakery posts "40 loaves, gone by 9pm," the
three nearest receiving sites get a text, first to claim it wins, a volunteer driver gets the
address. No accounts, no app store, works on a flip phone.

**Fill in before pasting:** `[CITY]`, `[COUNTY]`, `[TIMEZONE]`, `[ORG]` (the food bank or
mutual aid group you're building this with — if none yet, write "no partner org yet" and the
prompt handles it).

---

```text
You are building a surplus food rescue dispatch tool for [CITY], [COUNTY]. Build it now;
do not ask me clarifying questions. Where you need a decision I did not make, choose the
option that best serves the person described below, state your choice in one line, and keep
going.

=== THE PERSON ===

Marisol closes a bakery in [CITY] at 8:00pm. She has roughly 40 loaves, 2 trays of pastry,
and a half sheet cake that are unsellable tomorrow. Today she throws them out, because the
one time she called a shelter it rang for six minutes and then she had to lock up.

Twenty minutes away, a shelter kitchen coordinator named Dev is planning tomorrow's
breakfast for 60 people and has no bread. Dev has an Android phone from 2019 and does most
of his work by text because he is standing up all day.

Neither of them will download an app. Neither will create an account. Marisol has ninety
seconds of attention at 8pm, not five minutes.

=== THE PROBLEM, WITH A NUMBER ===

The binding constraint is time-to-match, not matching. Prepared and baked goods have a
usable window measured in hours; a match made the next morning is worth zero. The system's
job is to get from "Marisol has surplus" to "a named person is coming at a named time" in
under 15 minutes, at 8pm, without a phone call.

Assume nothing about volume. Design for 1 to 15 posts a day.

=== WHAT SUCCESS LOOKS LIKE ===

Marisol posts in under 90 seconds from a bookmarked page, and gets a text back within 15
minutes saying who is coming and when — or a clear "no takers, here's the compost drop-off,"
which is also a success.

=== BUILD THIS ===

Five surfaces. Build them in this order.

1. POST SURPLUS — a single page at /post, designed to be bookmarked on a phone home screen.
   No login. Fields, in this order, all on one screen, no wizard:
   - What is it (free text, one line, placeholder "40 loaves + pastry")
   - How much (a segmented control: "a bag or two" / "a few boxes" / "a car's worth" /
     "needs a truck" — NOT pounds; donors do not know pounds)
   - Ready until (time picker defaulting to 2 hours from now, with quick buttons: +1h, +2h,
     end of day)
   - Needs refrigeration? (yes/no toggle)
   - Contains allergens? (checkbox row: milk, egg, wheat, soy, peanut, tree nut, fish,
     shellfish, sesame — the 9 US major allergens)
   - Pickup address (pre-filled if they've posted before, from localStorage)
   - Your phone (pre-filled from localStorage; used only to text them the match)
   Submit button says "Post it" and is reachable without scrolling on a 360x640 viewport.
   After submit: a confirmation screen with the post, a big "Cancel this post" button, and
   the sentence "We'll text you when someone claims it."

2. CLAIM — receiving sites get an SMS: "SURPLUS: 40 loaves + pastry, ready until 9:00pm,
   1.2 mi from you, [CITY] — reply YES to claim, or open <short link>." Replying YES claims
   it atomically; the second YES gets "Sorry, already claimed by North Street Shelter."
   The short link opens a page with the full details, a map pin, and a Claim button.
   Claiming requires no login: the link contains a signed token tied to that recipient.

3. RECIPIENT SIGNUP — /join, where a site registers once: name, address, phone, what they
   can accept (refrigeration available y/n, max size they can handle, allergen restrictions,
   whether they can accept prepared food), and their receiving hours per weekday. An admin
   approves them before they get texts. Approval is a link in an email to the admin, not a
   dashboard.

4. DISPATCH BOARD — /board, a read-only page showing today's posts and their status
   (OPEN / CLAIMED by whom / PICKED UP / EXPIRED / CANCELED), auto-refreshing every 30
   seconds. This is what the coordinator leaves open on a laptop. No login required to view,
   but it shows no phone numbers or exact addresses to anonymous viewers — those appear only
   with the coordinator's link.

5. DRIVER HANDOFF — when a claim needs transport, the claimer taps "I need a driver," which
   texts the volunteer driver list in order of proximity, one at a time, 4 minutes apart,
   until one replies YES. First responder gets both addresses and both phone numbers. This
   is the single most valuable feature; do not cut it, but build it last so 1-4 ship first.

=== MATCHING LOGIC (be exact) ===

When a post is created, select recipients where ALL of the following hold:
  - approved = true
  - refrigeration_available >= post.needs_refrigeration
  - post is within their receiving hours for right now, in [TIMEZONE]
  - their max_size >= post.size
  - the post's allergens do not intersect their hard restrictions
  - distance <= 15 miles (straight-line is fine; do not build routing)
Rank by: (1) whether they're currently open, (2) distance ascending, (3) fewest claims
received in the last 7 days — this last one matters, it keeps one big org from absorbing
everything and starving the small ones.
Notify the top 3 immediately. If no claim in 10 minutes, notify the next 5. If no claim
15 minutes before "ready until," text the donor: "No takers tonight. Nearest compost/food
scrap drop-off: <address>." Then mark EXPIRED.

=== DATA MODEL ===

donors: id, phone (E.164), name, address, lat, lng, created_at, last_post_at
recipients: id, name, phone, email, address, lat, lng, refrigeration bool, max_size enum,
  accepts_prepared bool, allergen_restrictions text[], hours jsonb (per-weekday open/close),
  approved bool, approved_at, claims_last_7d int (computed, not stored)
posts: id, donor_id, description, size enum, needs_refrigeration bool, allergens text[],
  ready_until timestamptz, address, lat, lng, status enum(open|claimed|picked_up|expired|
  canceled), created_at, canceled_at
claims: id, post_id UNIQUE, recipient_id, claimed_at, picked_up_at, no_show bool
notifications: id, post_id, recipient_id, sent_at, channel, delivered bool, token
drivers: id, name, phone, service_area_lat, service_area_lng, active bool
driver_requests: id, claim_id, driver_id, offered_at, accepted_at

The UNIQUE constraint on claims.post_id is the entire race-condition strategy. Two people
replying YES at the same second must resolve by database constraint, not application logic.
Write a test that fires 10 concurrent claims at one post and asserts exactly one wins.

=== STACK ===

- Next.js 15 (App Router) + TypeScript, deployed on a single small VPS or Fly.io
- PostgreSQL via Drizzle ORM. SQLite is acceptable for the demo but the concurrency test
  must run against Postgres.
- SMS: Twilio. Wrap it behind an interface `SmsProvider` with a `ConsoleSmsProvider`
  implementation that prints to stdout, selected automatically when TWILIO_* env vars are
  absent. The entire app must be demoable with zero credentials.
- Geocoding: Nominatim (OpenStreetMap) with a 1 req/sec rate limit and a descriptive
  User-Agent, per their usage policy. Cache every geocode result permanently by normalized
  address string. Distance: haversine, computed in SQL. Do not add a routing engine.
- No component library. Plain CSS with CSS custom properties. Total JS under 100KB gzipped.

=== HARD CONSTRAINTS ===

- The /post page must be fully usable with JavaScript disabled (progressive enhancement, real
  form POST). Marisol's phone is old and her connection at the back of the bakery is bad. If
  JS fails, she still posts.
- First contentful paint under 1.5s on Slow 4G throttling for /post. Measure it and report
  the number.
- SMS is the primary channel; the web UI is the enhancement. Every critical action (claim,
  cancel, driver accept) must be completable by replying to a text with a single word.
- WCAG 2.2 AA. Real <label> elements, 4.5:1 contrast minimum, visible focus, touch targets
  at least 44x44px. Run axe-core in CI and fail the build on violations.
- Reading level: 6th grade. No word longer than three syllables in any button or error
  message. "Post it," not "Submit donation listing."
- Phone numbers are the only personal data. Store them for 90 days past last activity, then
  purge with a scheduled job you actually write and test. No analytics. No third-party fonts.
  No CDN scripts.
- Every timestamp is stored UTC and displayed in [TIMEZONE]. Write a test that runs with
  TZ=UTC and TZ=[TIMEZONE] and asserts identical display output.

=== DO NOT BUILD ===

- No user accounts, passwords, OAuth, or password reset. Signed tokens in links, that's all.
- No native mobile app. No PWA install prompt.
- No photo uploads in v1. It doubles the failure surface at 8pm and Marisol won't do it.
- No ratings, reviews, badges, gamification, or leaderboards.
- No weight tracking, pounds-diverted counters, or impact dashboard in v1. Every food rescue
  project builds this first and it helps no one eat. Build it in v2 if a funder demands it.
- No routing, ETA prediction, or live driver tracking.
- No AI/LLM anything. The matching is six SQL conditions.
- No admin panel. The admin is one person with a database GUI and an approval email link.

=== ACCEPTANCE TESTS ===

Write these as automated tests. All must pass.

1. Posting with only description + size + ready_until succeeds; all other fields optional.
2. Ten concurrent claims on one post result in exactly one claims row and nine rejections.
3. A recipient with refrigeration=false is not notified for a post with
   needs_refrigeration=true.
4. A recipient closed at post time is excluded from the first notification wave but included
   in the second wave only if they've opened by then.
5. A recipient whose allergen_restrictions include "peanut" is not notified about a post
   whose allergens include "peanut."
6. Two recipients at equal distance, one with 5 claims this week and one with 0: the one with
   0 is notified first.
7. No claim within 10 minutes triggers the second notification wave to the next 5 recipients.
8. No claim by 15 minutes before ready_until sends the donor the compost fallback text and
   sets status=expired.
9. Replying "yes" (any case, with or without whitespace/punctuation) claims. Replying
   anything else sends a help message and does not claim.
10. Canceling a post after it's claimed texts the claimer immediately.
11. With TWILIO_* env vars unset, the whole flow completes and messages print to stdout.
12. With JS disabled, /post submits successfully and renders the confirmation page.
13. The purge job deletes donor phone numbers with no activity in 91 days and leaves 89-day
    ones intact.
14. Nominatim is called at most once per unique normalized address, ever.

=== MILESTONES ===

M0 — Post and board. A post created on /post appears on /board within 30 seconds.
  EXIT: you post from your own phone, standing outside, on cell data, in under 90 seconds.

M1 — Notify and claim, console SMS. Matching logic complete and tested.
  EXIT: all 14 acceptance tests pass with ConsoleSmsProvider.

M2 — Real SMS. Twilio wired, inbound webhook handling replies.
  EXIT: you text YES from a real phone and the claim lands in the database.

M3 — Driver relay. Sequential driver offers, 4 minutes apart.
  EXIT: a real driver accepts and receives both addresses.

M4 — One real donor, one real recipient, one week.
  EXIT: one actual pickup happens because of this tool. Nothing before this counts.

=== SAFETY + LEGAL ===

- Food donation liability in the US is addressed by the Bill Emerson Good Samaritan Food
  Donation Act, which protects good-faith donors of apparently wholesome food. Put a short,
  accurate note about this on /join and /post, in plain language, and link to the statute
  text. Do not overstate the protection and do not present it as legal advice. Verify the
  current text before quoting it — do not paraphrase from memory.
- The app must never advise on food safety. It displays the donor's own refrigeration answer
  and allergen checkboxes and nothing more. Add: "Receiving sites are responsible for
  inspecting food before serving it."
- Allergen checkboxes are informational, not a guarantee. State that explicitly next to them.
- Do not display donor addresses or phone numbers publicly on /board.
- If [ORG] is a real partner, their name goes on the site and their phone number is the
  human fallback on every page. If there is no partner org yet, put a prominent line on
  /post: "This is a volunteer-run tool, not an official service."

=== HOW TO REPORT BACK ===

When you finish a milestone, tell me: what runs, the actual measured FCP number, which
acceptance tests pass, and what you'd cut if you had half the time. If you could not verify
something — a Nominatim rate limit, a Twilio behavior, the statute text — say so explicitly
rather than implying you checked.
```

---

## Why it's shaped this way

**SMS-first is the whole design, not a channel choice.** Both ends of this transaction are
people standing up, doing physical work, at the end of a shift. Every food rescue platform
that required an app died of the same cause: the donor had ninety seconds and the app wanted
five minutes. Making every action completable by texting one word is the difference.

**The "fewest claims in 7 days" tiebreak is a fairness mechanism.** Without it, the largest
best-staffed recipient claims everything within minutes and the small sites that most need
the food stop getting notified — a matching system quietly becoming a concentration system.

**No pounds-diverted dashboard in v1** is deliberate and slightly contrarian. It's the first
thing funders ask for and the first thing every team builds; it also has never fed anyone.
Ship the pager, earn the metric later.

**Before you build:** call your local food bank and ask what they use today. Very often the
answer is a group text or a Facebook group, and the honest best move is to make *that* work
better rather than replacing it. If they have a system, ask what breaks at 8pm.
