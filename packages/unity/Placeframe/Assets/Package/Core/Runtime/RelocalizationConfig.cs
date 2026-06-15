using Unity.Mathematics;

namespace Placeframe.Core
{
    public static class RelocalizationConfig
    {
        public const double MinInlierRatio = 0.25;
        public const int MinInliers = 50;

        // Association gate bounds: motion-scaled translation (widens with VIO distance since last support)
        // plus a fixed rotation bound.
        public const double GateTranslationBaseMeters = 0.5;
        public const double GateTranslationRatePerMeter = 0.1;
        public const double GateRotationRadians = 5.0 * math.PI_DBL / 180.0;

        // Motion-diversity scoring: deltaScore = gain * min(vioDelta, cap). The base is zero on purpose —
        // a stationary hypothesis (vioDelta ~ 0) earns nothing, so a wrong aliasing fix confirmed only from
        // its one viewpoint can never clear the promotion margin. Only motion moves a hypothesis's score.
        public const double SupportRewardBase = 0.0;
        public const double SupportRewardGainPerMeter = 1.0;
        public const double SupportRewardCapMeters = 5.0;

        // Hard ceiling on a hypothesis score. Score is current belief strength, not lifetime evidence:
        // without a ceiling a leader that banks a large score during an early motion-rich stretch cannot
        // be overtaken for hundreds of queries after it goes stale. The cap bounds that lead so decay
        // unseats a stale leader in a bounded number of queries.
        public const double ScoreCap = 5.0;

        // Once per query, every hypothesis not supported that query loses a fraction of its score;
        // hypotheses below the floor are pruned (never the published leader). At 0.90 the score is an
        // ~10-query memory, so a leader that stops being confirmed decays below a freshly-supported
        // challenger in roughly that many queries.
        public const double ScoreDecayPerMeasurement = 0.90;
        public const double ScoreFloor = 0.05;
        public const double SpawnSeedScore = 0.1;

        // Sized so one query's clusters (localizer caps at 2) plus the leader and a surviving challenger
        // fit without pruning a live hypothesis mid-batch.
        public const int MaxHypotheses = 4;

        // Promotion hysteresis: a challenger replaces the leader only after exceeding its score by the
        // margin AND holding that lead for the dwell.
        public const double PromotionMargin = 2.0;
        public const float PromotionDwellSeconds = 2.0f;

        // Measurement quality protects survival and breaks a lopsided quality gap, without ceding the
        // motion-diversity core (which adjudicates between comparable-quality hypotheses). Motion-only
        // accounting otherwise lets a weak partial lock hold the published frame while a much stronger
        // candidate decays from its seed and is pruned before it can earn motion credit.
        //
        // A spawn's seed gains up to this bonus, scaled by how far its inlier count clears the gate. Kept
        // below PromotionMargin so a fresh strong spawn survives the decay window but cannot promote on the
        // seed alone — only motion promotes it.
        public const double SpawnQualityBonusMax = 0.5;

        // Inlier count at which the spawn quality bonus saturates (the gate floor is MinInliers = 50).
        public const double QualityBonusSaturationInliers = 1000.0;

        // A challenger may promote without the full score margin when it dominates the leader on quality by
        // these factors AND has earned real motion credit. The gap is deliberately large — the
        // weak-partial-vs-strong case, not two comparable aliases (which the margin path still arbitrates).
        public const double PromotionQualityDominanceFactor = 2.0;
        public const double PromotionInlierRatioMargin = 0.15;

        // Motion reward a quality-dominant challenger must hold above the largest possible seed before it
        // can promote — ~1 m of confirmed walk, so a single-viewpoint alias never takes the dominance path.
        public const double PromotionQualityMotionMinScore = 1.0;

        // Drift-correction deadband: the widest and narrowest divergence the published frame tolerates
        // before re-anchoring. The bar starts at max and collapses toward min with motion and time.
        public const double CorrectionTranslationMaxMeters = 1.0;
        public const double CorrectionTranslationMinMeters = 0.15;
        public const double CorrectionRotationMaxRadians = 5.0 * math.PI_DBL / 180.0;
        public const double CorrectionRotationMinRadians = 1.0 * math.PI_DBL / 180.0;

        // Scales that collapse a bar from max to min: each bar's progress is the saturated sum of its
        // motion fraction and the time fraction, so either alone reaches the minimum. Distance dominates;
        // the time term only bites when the device stands still.
        public const double CorrectionDistanceToMinMeters = 5.0;
        public const double CorrectionAngleToMinRadians = 3.0;
        public const double CorrectionTimeToMinSeconds = 60.0;

        // Fixed eased duration over which a triggered correction slews to the best estimate. Bootstrap and
        // operator override bypass it and set the frame instantaneously.
        public const float CorrectionSlewSeconds = 0.25f;

        // Seconds without an accepted measurement after which localization is reported lost (drives
        // the lost indicator in consuming UIs).
        public const float LocalizationLostSeconds = 5.0f;

        // Online VIO-scale compensation. The device's tracker under-reports motion by a roughly
        // constant factor (outdoor monocular-inertial VIO measures ~0.93 m per metre walked), so the
        // published frame is shifted by (1 - 1/ema) of the distance walked since the last re-anchor to
        // keep rendered camera-to-content distances metric. The factor is estimated live from the
        // filter's per-segment scaleRatio (vioDelta / mapDelta), so it self-tunes per device and per
        // environment — a tracker with no bias converges to 1.0 and the offset vanishes.
        //
        // Off on Magic Leap 2: its stereo tracker is expected to provide metric scale, its scaleRatio
        // distribution has not been characterised, and on a near-zero-bias device the estimate would be
        // dominated by map/PnP noise rather than real bias. It stays off there until a diagnostic run
        // confirms whether compensation is warranted. The scaleRatio diagnostics still log on ML2.
#if MAGIC_LEAP
        public const bool CompEnabled = false;
#else
        public const bool CompEnabled = true;
#endif

        // Below this estimated bias the offset is suppressed entirely, so a device whose tracker already
        // provides metric scale gets exactly zero compensation rather than chasing measurement noise
        // around 1.0. A real bias like the ~7% outdoor monocular case clears it comfortably.
        public const double CompDeadzone = 0.03;

        // The estimate holds at identity (no offset) until this many in-band ratio samples have been
        // folded in, so a cold session never applies a half-formed correction.
        public const int CompWarmupSamples = 6;

        // EMA weight per in-band sample. Low enough to reject per-measurement noise, high enough to
        // converge within a short walk.
        public const double CompEmaAlpha = 0.1;

        // Ratios outside this band are treated as VIO jumps / spurious segments and never reach the
        // EMA, so a tracking glitch cannot poison the estimate.
        public const double CompScaleRatioMin = 0.80;
        public const double CompScaleRatioMax = 1.25;

        // Safety rail on the applied offset magnitude. Normal walking stays well under this; it only
        // catches runaway from a poisoned estimate or an unbounded uncorrected stretch.
        public const double CompMaxOffsetMeters = 3.0;

        // The offset target is recomputed at localization cadence; the published offset eases toward
        // it over this duration each frame so it tracks smoothly between measurements.
        public const float CompOffsetEaseSeconds = 0.25f;
    }
}
