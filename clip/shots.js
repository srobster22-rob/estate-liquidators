// ===========================================================================
// clip/shots.js - the performance. Loaded into the page after proto3d boots.
//
// This is the only file that decides what the clip *shows*. It stages the room,
// then drives the camera, the dolly and the two scripted inputs (take, drop)
// against a clock. Everything else - whether the Curator marks you, where it
// walks, when your light dims - is the prototype's own logic reacting.
//
// Beat names and times match CLIP-SPEC.md 3. Change them in both places.
// ===========================================================================
(() => {
"use strict";

// ------------------------------------------------------------------ geography
// All in metres, matching proto3d's ROOMS. The whole take happens in `land`
// (tier 2) and the hall doorway that leads back toward the van.
const PLINTH   = {x: 30.0, z: -1.2};   // where the hero item sits, 2.5m from the door
const HALLDOOR = {x: 27.5, z:  0.0};   // land <-> hall
const CONSDOOR = {x: 37.5, z: -2.5};   // land <-> conservatory (deeper)
const START    = {x: 35.2, z:  1.4};
// The prototype's grab radius is 3.2 m measured in 3D, and an item on the floor is
// 1.17 m below the eye - so a spot 3.1 m away on the map is already out of reach.
// APPROACH is set to ~2.0 m horizontal, which is 2.3 m to the item itself.
const APPROACH = {x: 31.7, z: -0.15};
const AFTER    = {x: 32.6, z:  0.30};  // where you stand when it marks you
const RETREAT  = {x: 34.7, z:  1.7};   // pushed away from the door
// Where it waits when the house wakes up. Two constraints fight here: far enough
// that its 9.9 m walk to the plinth fills beat 5 (1.95 m/s in COLLECT), and not so
// far that it never enters the 11.5 m a dimmed flashlight reaches. This lands it
// visible from ~13.5 s - the reveal happens under the "cuts you off" line.
const CURATOR_HOLD = {x: 20.5, z: 1.0};
const CROSS    = {x: 37.9, z0: -3.4, z1: -0.4}; // the hook: it crosses the deep doorway
// A second piece, parked where the blind sweep will catch it. 4.6 m from the retreat
// mark: far enough not to steal the interaction prompt (3.2 m, measured in 3D), close
// enough that a dimmed flashlight still lights it. Beat 5 has nothing else to see.
const DRESS    = {x: 36.2, z: -2.6};

// Highest tier the hero piece may come from - a size cap, not a value cap, since
// proto3d sizes items by tier (0.26 / 0.34 / 0.42 m half-extent). It was 1 while the
// cargo sat in the middle of the frame; C10 moved it to the corner, so tier 2 costs
// far less screen than it used to and buys a much deeper pool to pick from.
const HERO_TIER = Number(new URLSearchParams(location.search).get("heroTier") || 2);

// Preference order for the hero piece: tainted first (the HUD grade the clip is
// written around), then malignant, then clean, and within a grade the biggest number.
// C14: the old picker asked for "best tainted at tier <= 1" and fell through to
// items[0] when the roll had none - which on 1 seed in 10 staged a $41 CLEAN piece and
// silently shipped a different clip. Never let a fallback be a shrug.
const GRADE_RANK = {tainted: 2, malignant: 1, clean: 0};

let hero = -1, dressIx = -1;

const S = {
  fps: 30,
  frames: 720,          // 24.0 s

  // -------------------------------------------------------------- staging
  setup(C){
    const d = C.d();

    // Hero item: the best piece the seed rolled inside the size cap, moved onto the
    // plinth by the door. Ranked by grade first so the HUD reads a grade worth being
    // nervous about, then by value.
    const items = d.list();
    const pick = items.filter(i => i.tier <= HERO_TIER)
                      .sort((a, b) => (GRADE_RANK[b.grade] - GRADE_RANK[a.grade]) ||
                                      (b.value - a.value))[0];
    hero = pick.ix;
    d.stage(hero, PLINTH.x, PLINTH.z);

    // Set dressing for the blind beat - the best clean piece, kept unappraised so it
    // reads as plain grey loot rather than a second story object.
    const dress = d.list().filter(i => i.ix !== hero && i.grade === "clean")
                          .sort((a, b) => b.value - a.value)[0];
    dressIx = dress ? dress.ix : -1;
    if (dress) d.stage(dressIx, DRESS.x, DRESS.z);

    // Clear anything that would sit inside the aim cone and steal the prompt,
    // and anything close enough to clutter the plinth read.
    for (const it of d.list()){
      if (it.ix === hero || it.ix === dressIx) continue;
      const near = Math.hypot(it.x - PLINTH.x, it.z - PLINTH.z) < 5.0;
      const inShot = it.x > 27.5 && it.x < 37.0 && Math.abs(it.z) < 5.0;
      if (near || (inShot && Math.hypot(it.x - START.x, it.z - START.z) < 3.4)) d.drop(it.ix);
    }

    d.putCurator(CROSS.x, CROSS.z0);
    C.snapTo(START.x, START.z, Math.atan2(CROSS.x - START.x, CROSS.z0 + 1.0 - START.z), 0.02);
    C.cam.k = 0.045;
    C.pos.k = 0.030;
    C.fade(1);
    C.vignette(0.20);
    C.caption(null);
    C.card(0);
  },

  // -------------------------------------------------------------- per frame
  update(t, C){
    const d = C.d(), g = C.g();

    // open on black for 1/3 s so an auto-replay reads as a cut
    C.fade(t < 0.34 ? 1 - C.ease(t / 0.34) : 0);

    // Between the hook and the mark it stands in the deep doorway. Left to its own
    // PATROL it wanders off and gets stuck against a wall, which reads as a bug on
    // camera; it is pinned here purely so the shot is repeatable.
    if (t >= 2.60 && t < 9.0) d.putCurator(CROSS.x, CROSS.z1);

    // After the drop it is nobody's problem any more and PATROL sends it off to a
    // random shelf, which empties the frame mid-payoff. Pinned at the plinth it
    // stands over the piece it came for - same rule, better shot.
    if (t >= 18.60) d.putCurator(PLINTH.x + 0.25, PLINTH.z + 0.15);

    // ---- 1. hook  0.0 - 3.0 -------------------------------------------
    if (t < 3.0){
      // It crosses the deep doorway, unhurried, minding its own collection.
      if (t < 2.60){
        const k = C.clamp((t - 0.30) / 2.30, 0, 1);
        d.putCurator(CROSS.x, C.lerp(CROSS.z0, CROSS.z1, k));
      }
      if (t < 1.9) C.lookAt(CROSS.x, C.lerp(CROSS.z0, CROSS.z1, C.clamp((t - 0.3) / 2.3, 0, 1)), 1.15);
      else { C.cam.k = 0.030; C.lookAt(PLINTH.x + 0.6, PLINTH.z + 0.3, 0.55); }
      // G7 wants a legible caption inside 0.4 s, so this one fades in fast.
      cap(C, t, 0.17, 2.90, `the monster in this house<br>isn't hunting <span class="hi">you</span>`, 5);
    }

    // ---- 2. bait  3.0 - 6.0 -------------------------------------------
    else if (t < 6.0){
      C.cam.k = 0.045; C.pos.k = 0.035;
      C.moveTo(APPROACH.x, APPROACH.z);
      C.frameAt(PLINTH.x, PLINTH.z, 0.50, -0.18);   // low in frame, room above it
      if (t >= 4.95) d.know(hero);              // the value resolves on screen
      cap(C, t, 3.20, 5.90, `it's hunting whatever<br>you're <span class="hi">picking up</span>`);
    }

    // ---- 3. take  6.0 - 9.0 -------------------------------------------
    else if (t < 9.0){
      C.cam.k = 0.055; C.pos.k = 0.035;
      if (!this._took && t >= 6.35){ g.grab(); this._took = true; }
      C.moveTo(AFTER.x, AFTER.z);
      // straighten up off the floor and turn toward the way home. From here on the
      // cargo owns the bottom of the frame, so everything worth seeing is framed high.
      const k = C.ease((t - 6.6) / 2.2);
      C.frameAt(C.lerp(PLINTH.x, HALLDOOR.x - 1.0, k), C.lerp(PLINTH.z, HALLDOOR.z + 0.2, k),
                C.lerp(0.55, 1.30, k), C.lerp(-0.18, 0.10, k));
      C.caption(null);
    }

    // ---- 4. mark  9.0 - 13.0 ------------------------------------------
    else if (t < 13.0){
      C.cam.k = 0.050; C.pos.k = 0.028;
      if (!this._marked){
        d.putCurator(CURATOR_HOLD.x, CURATOR_HOLD.z);   // it was always down there
        d.meter(92);                                    // COLLECT: the house is awake
        this._marked = true;
      }
      // Keep the dolly moving even with nothing on screen - a still frame in a dark
      // shot is indistinguishable from a dropped frame, and G6 is right to fail it.
      // Once the cargo moved out of centre frame (C10) this beat had nothing left in
      // it at all, so the move is bigger now and the aim drifts across the doorway.
      C.moveTo(C.lerp(AFTER.x, AFTER.x + 1.5, C.ease((t - 9.0) / 4.0)),
               C.lerp(AFTER.z, AFTER.z + 1.1, C.ease((t - 9.0) / 4.0)));
      // Framed clear of the cargo (top edge ~y1009) but still well inside the beam.
      // The dimmed cone's falloff is not linear: up 0.22 sits 8.1 deg off-axis and
      // keeps 87% of on-axis intensity, where C4's 0.32 kept only 73% and lost the
      // shot. C5 over-corrected to 0.12 and gave the frame away for 8% of light.
      // One slow pass off the doorway and across the near east wall (~4 m), which is
      // close enough to light up properly, then back toward the door for beat 5.
      const k4 = 0.5 - 0.5 * Math.cos((t - 9.0) * 1.05);
      C.frameAt(C.lerp(HALLDOOR.x - 1.2, 36.5, k4), C.lerp(HALLDOOR.z + 0.5, -1.6, k4),
                C.lerp(1.25, 1.05, k4), 0.08);
      C.vignette(0.20 + 0.24 * C.ease((t - 9.0) / 1.6));
      cap(C, t, 9.55, 12.85, `your light dims<br>when it's <span class="hi">you</span>`);
    }

    // ---- 5. blind  13.0 - 17.5 ----------------------------------------
    // It is walking to the plinth right now and you cannot see it. A dimmed light
    // is both shorter (19m -> 11.5m) and tighter, so at COLLECT range the Curator
    // is effectively invisible - the tell that warns you also blinds you. The shot
    // is a nervous sweep of the room, which is the only honest thing to film here.
    else if (t < 17.5){
      C.cam.k = 0.085; C.pos.k = 0.050;   // faster dolly: parallax is the only motion here
      C.moveTo(RETREAT.x, RETREAT.z);                   // pushed away from the door
      // Sweep between the dark doorway you came from and the near corner. The far end
      // of the arc is black - that is the point - but the near end catches a wall at
      // ~2.5 m and the dressing piece at ~4.6 m, both of which a dimmed light still
      // reaches. Aiming the sweep at 6-8 m surfaces (as C5 did) lights nothing.
      // Aim the near end of the sweep into the corner. Tried aiming *past* the
      // dressing piece so it would clear the cargo (which owns the middle +/-16.5
      // deg): that points into open floor and lights nothing. A wall at 2.5 m is
      // the only thing a dimmed flashlight reliably brings back.
      const sweep = 0.5 + 0.5 * Math.sin((t - 13.0) * 1.15 - 1.5);
      C.frameAt(C.lerp(28.5, DRESS.x, sweep), C.lerp(-1.5, DRESS.z, sweep),
                C.lerp(1.35, 0.55, sweep), 0.08 + 0.07 * Math.sin((t - 13.0) * 0.8));
      // Two lines, because the picture cannot carry this beat: the first is what you
      // see (nothing), the second is the rule the reveal is about to prove.
      if (t < 15.5) cap(C, t, 13.25, 15.40, `and now you can't<br>see it <span class="hi">coming</span>`);
      else cap(C, t, 15.60, 17.30, `it's walking to the shelf<br>you <span class="hi">took it from</span>`);
    }

    // ---- 6. drop  17.5 - 21.0 -----------------------------------------
    // The payoff. You put it down, the aggro clears, the light goes back to full
    // range - and it is standing on the plinth between you and the door, which is
    // where it has been walking for the last six seconds.
    else if (t < 21.0){
      C.cam.k = t < 18.0 ? 0.060 : 0.130;   // whip round to it as the light returns
      C.pos.k = 0.022;
      if (!this._dropped && t >= 17.95){ g.grab(); this._dropped = true; }
      C.moveTo(RETREAT.x + 0.5, RETREAT.z + 0.4);
      const c = d.curator();
      C.frameAt(c.x, c.z, 1.15, C.lerp(0.14, 0.05, C.ease((t - 18.1) / 1.6)));
      C.vignette(C.lerp(0.44, 0.20, C.ease((t - 18.0) / 1.4)));
      // clear the game's chrome before the card arrives, not underneath it
      C.chrome(1 - C.ease((t - 20.30) / 0.55), 1 - C.ease((t - 20.05) / 0.45));
      if (t < 19.35) cap(C, t, 18.25, 19.35, `so <span class="hi">put it down</span> —`);
      else cap(C, t, 19.50, 20.90, `or hand it to<br><span class="hi">your friend</span>`);
    }

    // ---- 7. card  21.0 - 24.0 -----------------------------------------
    else {
      C.cam.k = 0.022; C.pos.k = 0.014;
      C.caption(null);
      C.moveTo(RETREAT.x + 1.1, RETREAT.z + 0.9);
      const it = d.list()[hero];
      C.frameAt(it.x, it.z, 0.45, -0.52);   // the piece back on the floor, card above
      const k = C.ease((t - 21.15) / 0.9);
      C.chrome(0, 0);                              // the card gets the frame to itself
      C.card(k);
      C.vignette(0.20 + 0.34 * k);
      if (t > 23.55) C.fade(C.ease((t - 23.55) / 0.45) * 0.55);
    }
  }
};

// Caption with an 8-frame fade at each end (override with `fade`), so nothing pops.
function cap(C, t, from, to, html, fade){
  if (t < from || t > to){ if (t > to) C.caption(null); return; }
  const F = (fade === undefined ? 8 : fade) / S.fps;
  const a = Math.min(C.ease((t - from) / F), C.ease((to - t) / F));
  C.caption(html, {alpha: +a.toFixed(3), top: 1150});
}

window.__shots = S;
})();
