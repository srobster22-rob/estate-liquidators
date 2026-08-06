// DESIGN.md 6.5 - the pacing spine.
//
// This is a fast-decaying NOISE LEVEL plus a slowly ratcheting FLOOR, not an
// accumulator. The accumulator version does not work at any decay rate: gross
// gain from ordinary play is ~54/min against a 100-point scale, so the meter
// saturates inside a minute and stays pinned for the rest of the night, for
// every crew including one that never makes a sound. Sweeping decay from 1 to
// 22/min barely moves it. See LOOP_LOG R3.
//
// Decay SCALES WITH CREW SIZE. The 50/min figure was tuned against four players.
// A solo player generates about a quarter of that noise, so 50/min swamps
// everything they do and the meter never leaves DORMANT. Every simulation in
// this project ran four players, so the dependency stayed invisible until the
// prototype was actually played - LOOP_LOG R12.

using System;

namespace EstateLiquidators.Core
{
    public enum CuratorTier { Dormant, Patrol, Pursue, Collect }

    public sealed class Disturbance
    {
        public const float DecayPerMinAtCrew4 = 50f;
        public const float RatchetEnd = 55f;          // floor climbs 0 -> 55 over a night
        public const float PerCursedItemFloor = 7f;   // LOOP_LOG R9, up from an inert 2

        public const float PatrolAt = 30f, PursueAt = 60f, CollectAt = 85f;

        // The three levers, named rather than inlined so the drift checker can
        // see them. A magic number in a method body is a constant nothing is
        // guarding - LOOP_LOG R16.
        public const float LightWingGain = 25f;
        public const float KillLightsRelief = 15f;
        public const float GoQuietRelief = 20f;

        readonly int _crew;
        readonly float _nightSeconds;

        public float Value { get; private set; }
        public float Elapsed { get; private set; }

        public Disturbance(int crew, float nightSeconds)
        {
            if (crew < 1) throw new ArgumentOutOfRangeException(nameof(crew));
            _crew = crew;
            _nightSeconds = nightSeconds;
        }

        public float DecayPerSecond => DecayPerMinAtCrew4 * (_crew / 4f) / 60f;

        public float Floor(int cursedInVan) =>
            RatchetEnd * Math.Clamp(Elapsed / _nightSeconds, 0f, 1f)
            + cursedInVan * PerCursedItemFloor;

        public void AddNoise(NoiseKind k, float dt) =>
            Value = MathF.Min(100f, Value + Loudness.DisturbanceGain(k, dt));

        /// <summary>Ghost Static: every point spent is +1 Disturbance. DESIGN 5.1.</summary>
        public void AddStatic(int points) =>
            Value = MathF.Min(100f, Value + points);

        public void Tick(float dt, int cursedInVan)
        {
            Elapsed += dt;
            Value = MathF.Max(Floor(cursedInVan),
                    MathF.Min(100f, Value - DecayPerSecond * dt));
        }

        /// <summary>Lever: kill the lights. DESIGN 6.5.</summary>
        public void KillLights() => Value = MathF.Max(0f, Value - KillLightsRelief);

        /// <summary>Lever: 45 seconds of crew-wide quiet.</summary>
        public void GoQuiet() => Value = MathF.Max(0f, Value - GoQuietRelief);

        public void LightWing() => Value = MathF.Min(100f, Value + LightWingGain);

        public CuratorTier Tier =>
            Value >= CollectAt ? CuratorTier.Collect :
            Value >= PursueAt ? CuratorTier.Pursue :
            Value >= PatrolAt ? CuratorTier.Patrol : CuratorTier.Dormant;

        public static float RetrievalChance(CuratorTier t) => t switch
        {
            CuratorTier.Patrol => 0.02f,
            CuratorTier.Pursue => 0.10f,
            CuratorTier.Collect => 0.25f,
            _ => 0f,
        };
    }

    /// <summary>
    /// ECONOMY.md 1 and DESIGN.md 4.2. Van capacity is the master balance
    /// constant: the appraiser's edge decays monotonically as the van grows and
    /// hits zero somewhere between 24 and 32 slots. The ceiling is a design
    /// guarantee, not a tuning knob.
    /// </summary>
    public static class Van
    {
        public const int BaseSlots = 14;
        public const int MaxSlots = 20;

        public static float Slots(WeightClass c) => c switch
        {
            WeightClass.Pocket => 0.5f,
            WeightClass.Armful => 1.0f,
            WeightClass.TwoMan => 3.0f,
            WeightClass.Cart => 5.0f,
            _ => 1.0f,
        };

        /// <summary>
        /// The curse's van cost is a TAIL RISK, not a fee. A linear cost cannot
        /// balance a multiplicative benefit - taking every cursed item won at x6,
        /// x4, x3, x2.5 and x2.0 value, a step function with no interesting
        /// middle. Ruin probability is the one cost that grows faster than the
        /// benefit, and it produces a real interior optimum at two to three
        /// pieces. LOOP_LOG R10-R11.
        /// </summary>
        public const float RuinK = 0.015f, RuinExp = 1.8f;

        public static float RuinChance(int cursedAboard) =>
            cursedAboard <= 0 ? 0f
            : MathF.Min(0.95f, RuinK * MathF.Pow(cursedAboard, RuinExp));
    }

    public enum WeightClass { Pocket, Armful, TwoMan, Cart }
}
