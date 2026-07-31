// Cross-checks the C# core against the numbers the Python simulations produced.
// A port that merely compiles is not a port that agrees; this project has burned
// three "verified" figures that turned out to be instrumentation bugs, so the
// rules that matter get pinned by assertions.
//
//   dotnet run --project unity/tests/CoreTests

using System;
using System.Collections.Generic;
using System.Linq;
using EstateLiquidators.Core;

static class T
{
    static int _fail;
    public static void Check(string name, bool ok, string detail = "")
    {
        Console.WriteLine($"  {(ok ? "PASS" : "FAIL")}  {name}{(detail.Length > 0 ? "   " + detail : "")}");
        if (!ok) _fail++;
    }
    public static void Near(string name, float got, float want, float tol,
                            string detail = "")
        => Check(name, MathF.Abs(got - want) <= tol,
                 $"got {got:0.###}, want {want:0.###}"
                 + (detail.Length > 0 ? " - " + detail : ""));
    public static int Exit => _fail;
    public static void Head(string s) => Console.WriteLine($"\n{s}\n{new string('-', 74)}");
}

sealed class Item : ICarried
{
    public float AppraisedValue { get; init; }
    public CurseGrade Grade { get; init; } = CurseGrade.Clean;
}

sealed class Player : IAttentionSubject
{
    public List<ICarried> Items = new();
    public IReadOnlyList<ICarried> Carried => Items;
    public int NoiseEventsLast10s { get; set; }
    public bool LightVisible { get; set; }
    public string Name = "";
    public override string ToString() => Name;
}

class Program
{
    static int Main()
    {
        T.Head("LOUDNESS  (AUDIO-SPEC 1.1-1.2)");
        T.Near("appraiser ping -> Disturbance",
            Loudness.DisturbanceGain(NoiseKind.AppraisePing, 0f), 4.32f, 0.001f);
        T.Near("small breakage -> Disturbance",
            Loudness.DisturbanceGain(NoiseKind.BreakSmall, 0f), 8.1f, 0.001f);
        T.Near("Curator hears breakage at",
            Loudness.HearingRadius(NoiseKind.BreakSmall), 29.7f, 0.05f);
        T.Near("Curator hears a walk at",
            Loudness.HearingRadius(NoiseKind.Walk), 6.6f, 0.05f);
        T.Check("walking costs no Disturbance",
            Loudness.DisturbanceGain(NoiseKind.Walk, 1f) > 0
              && !Loudness.IsSustained(NoiseKind.Walk),
            "impulse-only; never charged per second");
        T.Near("sprint sustained is per second, not per frame",
            Loudness.DisturbanceGain(NoiseKind.Sprint, 1f / 60f), 0.9f / 60f, 0.0001f);
        T.Check("shouting is louder than a door slam",
            Loudness.Of(NoiseKind.VoiceShout) > Loudness.Of(NoiseKind.DoorSlam));
        T.Check("appraising is louder than sprinting",
            Loudness.Of(NoiseKind.AppraisePing) > Loudness.Of(NoiseKind.Sprint));

        // R19: EffectiveAt had no assertion at all, so swapping the two occlusion
        // coefficients or deleting the range clamp was invisible to every guard.
        T.Check("the Curator hears through walls better than a player does",
            Loudness.EffectiveAt(NoiseKind.BreakSmall, 10f, 2, curator: true)
              > Loudness.EffectiveAt(NoiseKind.BreakSmall, 10f, 2, curator: false),
            "occlusion 0.85 vs 0.60 per wall");
        T.Near("...and each wall costs the Curator 15%",
            Loudness.EffectiveAt(NoiseKind.BreakSmall, 10f, 1, curator: true)
              / Loudness.EffectiveAt(NoiseKind.BreakSmall, 10f, 0, curator: true),
            0.85f, 0.001f);
        T.Check("sound does not carry past its radius, or go negative",
            Loudness.EffectiveAt(NoiseKind.BreakSmall, 40f, 0, curator: true) == 0f
              && Loudness.EffectiveAt(NoiseKind.Walk, 100f, 0, curator: false) == 0f,
            "radius is 29.7m at L90");

        T.Head("ATTENTION  (TECH-SPEC A3, corrected in LOOP_LOG R2)");
        var empty = new Player { Name = "empty", NoiseEventsLast10s = 3, LightVisible = true };
        T.Near("empty-handed player weighs nothing", Attention.Weight(empty), 0f, 0.0001f);

        var loaded = new Player { Name = "loaded" };
        loaded.Items.Add(new Item { AppraisedValue = 150 });
        T.Check("...even against the cheapest loot in the game",
            Attention.Weight(loaded) > Attention.Weight(empty),
            "$150 beats a loud lit player carrying nothing");

        var mal = new Player { Name = "mal" };
        mal.Items.Add(new Item { AppraisedValue = 100, Grade = CurseGrade.Malignant });
        T.Near("malignant scales attention x3", Attention.Weight(mal), 300f, 0.01f);

        var lit = new Player { Name = "lit", LightVisible = true };
        lit.Items.Add(new Item { AppraisedValue = 100 });
        T.Near("light multiplies by 1.30", Attention.Weight(lit), 130f, 0.01f);

        // R19: every attention assertion above used a player with ZERO noise events,
        // so noise could be made additive again - the exact R2 bug, BUILD-PROMPT's
        // first non-negotiable - without a single test noticing, as long as the
        // empty-handed guard survived. These pin the multiplicative shape itself.
        var noisy = new Player { Name = "noisy", NoiseEventsLast10s = 3 };
        noisy.Items.Add(new Item { AppraisedValue = 100 });
        T.Near("noise multiplies a carrier by 1 + 0.20/event",
            Attention.Weight(noisy), 160f, 0.01f);

        var noisyRich = new Player { Name = "noisyRich", NoiseEventsLast10s = 3 };
        noisyRich.Items.Add(new Item { AppraisedValue = 200 });
        T.Near("doubling the loot doubles the weight at identical noise",
            Attention.Weight(noisyRich) / Attention.Weight(noisy), 2f, 0.0001f,
            "the signature of multiplicative: an additive term would not scale");

        T.Head("HAND-OFF  (0.0s with the override, 6.0s without)");
        var a = new Player { Name = "A" }; a.Items.Add(new Item { AppraisedValue = 1000 });
        var b = new Player { Name = "B" }; b.Items.Add(new Item { AppraisedValue = 300 });
        var crew = new List<IAttentionSubject> { a, b };

        var sel = new AttentionSelector();
        sel.Update(0f, crew);
        T.Check("locks onto the richest carrier", ReferenceEquals(sel.Target, a));

        // Pass the prize 2s in - inside the 8s commitment lock.
        var prize = a.Items[0]; a.Items.Clear(); b.Items.Add(prize);
        sel.Update(2f, crew, handoffFrom: a, handoffTo: b);
        T.Check("hand-off retargets instantly through the lock",
            ReferenceEquals(sel.Target, b), "0.0s");

        var sel2 = new AttentionSelector();
        var a2 = new Player { Name = "A" }; a2.Items.Add(new Item { AppraisedValue = 1000 });
        var b2 = new Player { Name = "B" }; b2.Items.Add(new Item { AppraisedValue = 300 });
        var crew2 = new List<IAttentionSubject> { a2, b2 };
        sel2.Update(0f, crew2);
        var p2 = a2.Items[0]; a2.Items.Clear(); b2.Items.Add(p2);
        // Record WHEN the retarget landed, not where the loop counter ended up -
        // incrementing after the successful Update reads one tick late.
        float handoffAt = 2f, retargetAt = float.NaN;
        for (float now = handoffAt; now <= 24f; now += 1f)
        {
            sel2.Update(now, crew2);
            if (ReferenceEquals(sel2.Target, b2)) { retargetAt = now; break; }
        }
        T.Near("without the override it waits out the lock",
            retargetAt - handoffAt, 6f, 0.5f);

        // R19: the override fired on any hand-off, not just one FROM the target, and
        // nothing caught it. A pass between two bystanders must not steal the Curator
        // off the person actually holding the prize.
        var sel4 = new AttentionSelector();
        var rich = new Player { Name = "rich" };
        rich.Items.Add(new Item { AppraisedValue = 1000 });
        var by1 = new Player { Name = "by1" }; by1.Items.Add(new Item { AppraisedValue = 100 });
        var by2 = new Player { Name = "by2" };
        var crew3 = new List<IAttentionSubject> { rich, by1, by2 };
        sel4.Update(0f, crew3);
        var trinket = by1.Items[0]; by1.Items.Clear(); by2.Items.Add(trinket);
        sel4.Update(2f, crew3, handoffFrom: by1, handoffTo: by2);
        T.Check("a hand-off between bystanders does not steal the Curator",
            ReferenceEquals(sel4.Target, rich),
            "only a pass FROM the current target overrides hysteresis");

        T.Head("NO FLICKER  (comparable loot, 300s)");
        var rng = new Random(7);
        var four = Enumerable.Range(0, 4).Select(i =>
        {
            var p = new Player { Name = "P" + i };
            p.Items.Add(new Item { AppraisedValue = 400 + (float)rng.NextDouble() * 500 });
            return p;
        }).ToList();
        var crew4 = four.Cast<IAttentionSubject>().ToList();
        var sel3 = new AttentionSelector();
        for (float now = 0; now < 300; now += 2f)
        {
            foreach (var p in four)
            {
                p.NoiseEventsLast10s = rng.NextDouble() < 0.25 ? 1 : 0;
                p.LightVisible = rng.NextDouble() < 0.5;
            }
            sel3.Update(now, crew4);
        }
        float perMin = sel3.Retargets / 5f;
        T.Check($"retargets/min = {perMin:0.0} (python measured 2.7)",
            perMin > 0.5f && perMin < 6f, "decisive, not frantic");

        T.Head("DISTURBANCE  (DESIGN 6.5, tuned R4, crew-scaled R12)");
        T.Near("decay at crew 4", new Disturbance(4, 720).DecayPerSecond, 50f / 60f, 0.001f);
        T.Near("decay at crew 1 is a quarter", new Disturbance(1, 720).DecayPerSecond,
            12.5f / 60f, 0.001f);

        var d = new Disturbance(4, 720);
        for (int i = 0; i < 720; i++) d.Tick(1f, 0);
        T.Near("floor ratchets to 55 by sunrise", d.Value, 55f, 0.5f);

        var d2 = new Disturbance(4, 720);
        for (int i = 0; i < 360; i++) d2.Tick(1f, 0);
        float before = d2.Value;
        for (int i = 0; i < 30; i++) d2.AddNoise(NoiseKind.AppraisePing, 0f);
        T.Check("30 appraisals push it into PURSUE",
            d2.Tier == CuratorTier.Pursue || d2.Tier == CuratorTier.Collect,
            $"{before:0} -> {d2.Value:0} ({d2.Tier})");

        var d3 = new Disturbance(4, 720);
        for (int i = 0; i < 60; i++) d3.AddNoise(NoiseKind.BreakSmall, 0f);
        float peak = d3.Value;
        for (int i = 0; i < 120; i++) d3.Tick(1f, 0);
        T.Check("and going quiet genuinely drains it",
            d3.Value < peak - 40f, $"{peak:0} -> {d3.Value:0} over 2 min");

        T.Near("cursed cargo lifts the floor 7/item", new Disturbance(4, 720).Floor(3),
            21f, 0.01f);

        // R19: three Disturbance invariants nothing was checking.
        var d4 = new Disturbance(4, 720);
        for (int i = 0; i < 900; i++) d4.Tick(1f, 0);   // 3 minutes past sunrise
        T.Near("the ratchet stops at sunrise, it does not keep climbing",
            d4.Value, 55f, 0.5f, "Elapsed/night is clamped to 1");

        var d5 = new Disturbance(4, 720);
        for (int i = 0; i < 40; i++) d5.AddNoise(NoiseKind.BreakLarge, 0f);
        T.Check("Disturbance is capped at 100", d5.Value <= 100f,
            $"40 large breakages = {40 * 9}pts raw -> {d5.Value:0}");

        var d6 = new Disturbance(4, 720);
        d6.AddStatic(5);
        T.Near("ghost Static costs 1 Disturbance per point", d6.Value, 5f, 0.001f,
            "DESIGN 5.1 - the dead player's budget was untested until R19");

        T.Head("ECONOMY  (ECONOMY.md, curse tail risk from R11)");
        T.Near("armful costs one slot", Van.Slots(WeightClass.Armful), 1f, 0.001f);
        T.Near("cart costs five", Van.Slots(WeightClass.Cart), 5f, 0.001f);
        T.Check("van ceiling is 20", Van.MaxSlots == 20, "appraiser dies at 24-32");
        T.Near("1 cursed piece is a shrug", Van.RuinChance(1) * 100f, 1.5f, 0.1f);
        T.Near("3 is the sweet spot", Van.RuinChance(3) * 100f, 10.8f, 0.3f);
        T.Near("5 is a quarter of your nights", Van.RuinChance(5) * 100f, 27.2f, 0.5f);
        T.Check("8 and you will not get away with it",
            Van.RuinChance(8) > 0.60f, $"{Van.RuinChance(8):P0}");
        // R19: uncapped, the curve passes 1.0 at 22 items and becomes a certainty.
        T.Near("ruin is capped at 95%, never a certainty", Van.RuinChance(30), 0.95f,
            0.0001f, "a van you cannot possibly extract is not a gamble");
        T.Near("malignant pays x6", Curse.Value(CurseGrade.Malignant), 6f, 0.001f);
        T.Near("...and costs 20% at the ledger", Curse.Fee(CurseGrade.Malignant), 0.20f, 0.001f);

        Console.WriteLine($"\n{new string('=', 74)}");
        Console.WriteLine(T.Exit == 0
            ? "ALL CHECKS PASSED - C# core agrees with the Python simulations."
            : $"{T.Exit} CHECK(S) FAILED");
        return T.Exit;
    }
}
