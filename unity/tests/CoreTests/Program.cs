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
    public static void Near(string name, float got, float want, float tol)
        => Check(name, MathF.Abs(got - want) <= tol, $"got {got:0.###}, want {want:0.###}");
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

        // D-23. Unrationed, the levers delete COLLECT outright: pull-on-sight is
        // five uses a night and 0% of the night in the top tier, against 14% on
        // the cooldown. The gate belongs to the model, not to a call site.
        var d4 = new Disturbance(4, 720);
        for (int i = 0; i < 60; i++) d4.AddNoise(NoiseKind.DoorSlam, 1f);
        float beforeLever = d4.Value;
        T.Check("go quiet works when the lever is ready", d4.GoQuiet());
        T.Near("...and relieves 20", beforeLever - d4.Value, 20f, 0.01f);
        T.Check("the crew is hushed afterwards", d4.Quiet);
        T.Near("hush scales noise to 0.35", d4.Hush, 0.35f, 0.001f);
        T.Check("a second pull is refused on cooldown", !d4.GoQuiet());
        T.Check("and so is the other lever - one valve, one cooldown",
            !d4.KillLights());
        for (int i = 0; i < 60; i++) d4.Tick(1f, 0);
        T.Check("still on cooldown after a minute", !d4.LeverReady);
        T.Check("the hush has expired after 45s", !d4.Quiet);
        for (int i = 0; i < 61; i++) d4.Tick(1f, 0);
        T.Check("ready again after 120s", d4.LeverReady);

        T.Head("ECONOMY  (ECONOMY.md, curse tail risk from R11)");
        T.Near("armful costs one slot", Van.Slots(WeightClass.Armful), 1f, 0.001f);
        T.Near("cart costs five", Van.Slots(WeightClass.Cart), 5f, 0.001f);
        T.Check("van ceiling is 20", Van.MaxSlots == 20, "appraiser dies at 24-32");
        T.Near("1 cursed piece is a shrug", Van.RuinChance(1) * 100f, 1.5f, 0.1f);
        T.Near("3 is the sweet spot", Van.RuinChance(3) * 100f, 10.8f, 0.3f);
        T.Near("5 is a quarter of your nights", Van.RuinChance(5) * 100f, 27.2f, 0.5f);
        T.Check("8 and you will not get away with it",
            Van.RuinChance(8) > 0.60f, $"{Van.RuinChance(8):P0}");
        T.Near("malignant pays x6", Curse.Value(CurseGrade.Malignant), 6f, 0.001f);
        T.Near("...and costs 20% at the ledger", Curse.Fee(CurseGrade.Malignant), 0.20f, 0.001f);

        Console.WriteLine($"\n{new string('=', 74)}");
        Console.WriteLine(T.Exit == 0
            ? "ALL CHECKS PASSED - C# core agrees with the Python simulations."
            : $"{T.Exit} CHECK(S) FAILED");
        return T.Exit;
    }
}
