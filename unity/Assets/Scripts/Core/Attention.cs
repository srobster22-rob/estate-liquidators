// TECH-SPEC.md A3 - Curator attention.
//
// The formula here is MULTIPLICATIVE and that is the whole point. The original
// additive version (+200/noise, +400/light) let an empty-handed player who was
// loud and lit be hunted 100% of the time in preference to three teammates
// actually carrying loot, which breaks design pillar 2 outright. Simulated in
// sim/curator_attention.py; corrected in LOOP_LOG R2.
//
// Carry nothing, weigh nothing. That makes the pillar arithmetically impossible
// to violate rather than a property we hope the constants preserve.

using System.Collections.Generic;

namespace EstateLiquidators.Core
{
    public enum CurseGrade { Clean, Tainted, Malignant }

    public static class Curse
    {
        /// <summary>Value multiplier. ECONOMY.md 3.</summary>
        public static float Value(CurseGrade g) => g switch
        {
            CurseGrade.Tainted => 2.5f,
            CurseGrade.Malignant => 6.0f,
            _ => 1.0f,
        };

        /// <summary>Attention multiplier. TECH-SPEC A3.</summary>
        public static float Attention(CurseGrade g) => g switch
        {
            CurseGrade.Tainted => 1.5f,
            CurseGrade.Malignant => 3.0f,
            _ => 1.0f,
        };

        /// <summary>Ledger fee taken at extraction. ECONOMY.md 5.</summary>
        public static float Fee(CurseGrade g) => g switch
        {
            CurseGrade.Tainted => 0.08f,
            CurseGrade.Malignant => 0.20f,
            _ => 0f,
        };
    }

    public interface ICarried
    {
        float AppraisedValue { get; }
        CurseGrade Grade { get; }
    }

    public interface IAttentionSubject
    {
        IReadOnlyList<ICarried> Carried { get; }
        int NoiseEventsLast10s { get; }
        bool LightVisible { get; }
    }

    public static class Attention
    {
        public const float NoisePerEvent = 0.20f;   // multiplier, not addend
        public const float LightMultiplier = 1.30f;

        public static float Weight(IAttentionSubject p)
        {
            float loot = 0f;
            var carried = p.Carried;
            for (int i = 0; i < carried.Count; i++)
                loot += carried[i].AppraisedValue * Curse.Attention(carried[i].Grade);

            if (loot <= 0f) return 0f;   // pillar 2, enforced by arithmetic

            float mult = 1f + NoisePerEvent * p.NoiseEventsLast10s;
            if (p.LightVisible) mult *= LightMultiplier;
            return loot * mult;
        }
    }

    /// <summary>
    /// Target selection with hysteresis. Raw highest-weight targeting makes the
    /// Curator pirouette between four players every tick and read as broken.
    /// </summary>
    public sealed class AttentionSelector
    {
        public const float StealThreshold = 1.25f;
        public const float CommitSeconds = 8.0f;

        public IAttentionSubject Target { get; private set; }
        public int Retargets { get; private set; }
        float _lockedUntil;

        public void Reset() { Target = null; _lockedUntil = 0f; Retargets = 0; }

        /// <summary>
        /// A hand-off is a first-class event that punches straight through both
        /// hysteresis rules. Measured at 0.0s with the override and 6.0s without,
        /// when the pass lands inside a commitment lock - and hand-offs usually do,
        /// because they follow the retarget that scared you into passing.
        /// </summary>
        public void Update(float now, IReadOnlyList<IAttentionSubject> players,
                           IAttentionSubject handoffFrom = null,
                           IAttentionSubject handoffTo = null)
        {
            if (handoffTo != null && ReferenceEquals(handoffFrom, Target))
            {
                if (!ReferenceEquals(Target, handoffTo))
                {
                    Target = handoffTo;
                    Retargets++;
                    _lockedUntil = now + CommitSeconds;
                }
                return;
            }

            IAttentionSubject best = null;
            float bestW = 0f;
            for (int i = 0; i < players.Count; i++)
            {
                float w = Attention.Weight(players[i]);
                if (best == null || w > bestW) { best = players[i]; bestW = w; }
            }
            if (best == null) return;

            if (Target == null)
            {
                if (bestW > 0f) { Target = best; _lockedUntil = now + CommitSeconds; }
                return;
            }

            if (now < _lockedUntil) return;

            float cur = Attention.Weight(Target);
            if (cur <= 0f) { Target = bestW > 0f ? best : null; return; }
            if (!ReferenceEquals(best, Target) && bestW > cur * StealThreshold)
            {
                Target = best;
                Retargets++;
                _lockedUntil = now + CommitSeconds;
            }
        }
    }
}
