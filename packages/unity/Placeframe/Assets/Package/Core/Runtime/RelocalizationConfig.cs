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
    }
}
