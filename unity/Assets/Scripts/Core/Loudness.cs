// Estate Liquidators - core rules, deliberately free of UnityEngine.
//
// Everything in this namespace is a pure function of its inputs so it can be
// compiled and tested outside the editor. That is not architectural purity for
// its own sake: this project has already shipped three "verified" numbers that
// turned out to be instrumentation bugs, so the rules that matter are the ones
// a test can pin down.
//
// AUDIO-SPEC.md section 1 - one authored number per event, three consumers.

namespace EstateLiquidators.Core
{
    public enum NoiseKind
    {
        CrouchWalk, Walk, Sprint, Dolly, Radio,
        AppraisePing, DoorSlam, Crowbar, BreakSmall, BreakLarge,
        VoiceWhisper, VoiceNormal, VoiceRaised, VoiceShout,
    }

    public static class Loudness
    {
        public const float HearingRadiusPerL = 0.33f;   // metres
        public const float ImpulseDisturbancePerL = 0.09f;
        public const float SustainedDisturbancePerL = 0.02f;   // per SECOND
        public const float OcclusionPlayer = 0.60f;    // per wall
        public const float OcclusionCurator = 0.85f;
        public const float LocalisationFuzzM = 3.0f;

        /// <summary>Authored loudness, 0-100. AUDIO-SPEC 1.2.</summary>
        public static float Of(NoiseKind k) => k switch
        {
            NoiseKind.CrouchWalk => 8,
            NoiseKind.VoiceWhisper => 8,
            NoiseKind.Walk => 20,
            NoiseKind.VoiceNormal => 25,
            NoiseKind.Dolly => 35,
            NoiseKind.Radio => 38,
            NoiseKind.Sprint => 45,
            NoiseKind.VoiceRaised => 45,
            NoiseKind.AppraisePing => 48,
            NoiseKind.DoorSlam => 60,
            NoiseKind.VoiceShout => 65,
            NoiseKind.Crowbar => 75,
            NoiseKind.BreakSmall => 90,
            NoiseKind.BreakLarge => 100,
            _ => 0,
        };

        /// <summary>
        /// Sustained sources are ONLY those the spec gives a per-second value.
        /// Walking is free. Charging for it makes the meter rise 1.6/s against a
        /// decay of 0.017/s and pins it inside a minute - see LOOP_LOG R3.
        /// </summary>
        public static bool IsSustained(NoiseKind k) =>
            k is NoiseKind.Sprint or NoiseKind.Dolly or NoiseKind.Radio;

        public static float HearingRadius(NoiseKind k) => Of(k) * HearingRadiusPerL;

        /// <summary>Disturbance contribution. dt is ignored for impulses.</summary>
        public static float DisturbanceGain(NoiseKind k, float dt) =>
            IsSustained(k)
                ? Of(k) * SustainedDisturbancePerL * dt
                : Of(k) * ImpulseDisturbancePerL;

        /// <summary>Effective loudness at a listener, through the portal graph.</summary>
        public static float EffectiveAt(NoiseKind k, float distanceM, int walls, bool curator)
        {
            float occ = curator ? OcclusionCurator : OcclusionPlayer;
            float l = Of(k);
            for (int i = 0; i < walls; i++) l *= occ;
            float max = Of(k) * HearingRadiusPerL;
            if (max <= 0f) return 0f;
            float falloff = 1f - distanceM / max;
            return falloff <= 0f ? 0f : l * falloff;
        }
    }
}
