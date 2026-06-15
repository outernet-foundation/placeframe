using NUnit.Framework;
using Unity.Mathematics;
using static Placeframe.Core.Tests.RelocalizationTestHelpers;

namespace Placeframe.Core.Tests
{
    public class DriftCorrectionControllerTests
    {
        private const double Tolerance = 1e-3;

        private static double4x4 Translation(double x) =>
            Double4x4.FromTranslationRotation(new double3(x, 0, 0), quaternion.identity);

        // Walk the device along +x feeding a constant in-band scale ratio, holding the best estimate on
        // the base so no correction fires, then settle the eased offset. Returns the controller.
        private static DriftCorrectionController WarmAndWalk(double ratio, int observations)
        {
            var controller = new DriftCorrectionController();
            controller.Set(double4x4.identity, double3.zero, 0f);

            for (var i = 1; i <= observations; i++)
                controller.Observe(double4x4.identity, new double3(i, 0, 0), quaternion.identity, ratio, i);

            controller.Advance(1f);
            return controller;
        }

        [Test]
        public void Compensation_AfterWarmup_ShiftsContentByMissingScaleFraction()
        {
            const double ratio = 0.93;
            var observations = RelocalizationConfig.CompWarmupSamples;

            var controller = WarmAndWalk(ratio, observations);

            // Offset = (1 - 1/ema) * distance from the anchor (the Set position, never re-anchored here).
            var expected = (1.0 - (1.0 / ratio)) * observations;
            Assert.That(controller.Current.c3.x, Is.EqualTo(expected).Within(Tolerance));
            Assert.That(expected, Is.LessThan(0.0), "biasInverse > 1 must pull content back along the walk");
        }

        [Test]
        public void Compensation_BeforeWarmup_AppliesNoOffset()
        {
            var controller = WarmAndWalk(0.93, RelocalizationConfig.CompWarmupSamples - 1);

            Assert.That(controller.Current.c3.x, Is.EqualTo(0.0).Within(Tolerance));
        }

        [Test]
        public void Compensation_NullRatio_LeavesEstimateAndOffsetUntouched()
        {
            var controller = new DriftCorrectionController();
            controller.Set(double4x4.identity, double3.zero, 0f);

            for (var i = 1; i <= RelocalizationConfig.CompWarmupSamples + 4; i++)
                controller.Observe(double4x4.identity, new double3(i, 0, 0), quaternion.identity, null, i);

            controller.Advance(1f);

            Assert.That(controller.Current.c3.x, Is.EqualTo(0.0).Within(Tolerance));
        }

        [Test]
        public void Compensation_RatioWithinDeadzone_AppliesNoOffset()
        {
            // 0.99 is a 1% bias, inside the 3% dead-zone — a metric-scale device gets exactly zero offset.
            var controller = WarmAndWalk(0.99, RelocalizationConfig.CompWarmupSamples + 4);

            Assert.That(controller.Current.c3.x, Is.EqualTo(0.0).Within(Tolerance));
        }

        [Test]
        public void Correction_WithAccumulatedOffset_PublishesContinuously()
        {
            var controller = WarmAndWalk(0.93, RelocalizationConfig.CompWarmupSamples);
            var beforeCorrection = controller.Current.c3.xyz;
            Assert.That(math.length(beforeCorrection), Is.GreaterThan(0.1), "test needs a real pre-offset");

            var farEstimate = Double4x4.FromTranslationRotation(new double3(10, 0, 0), quaternion.identity);
            var corrected = controller.Observe(farEstimate, new double3(7, 0, 0), quaternion.identity, 0.93, 7f);

            Assert.That(corrected, Is.True, "a 10 m divergence past the collapsed deadband must correct");

            // Observe sets up the slew but never republishes, so the published frame is unchanged at the
            // correction instant — no jump from the offset-anchor reset.
            Assert.That(math.length(controller.Current.c3.xyz - beforeCorrection), Is.EqualTo(0.0).Within(1e-9));

            // One tiny step eases base and offset together; the published frame moves only a sliver.
            controller.Advance(0.001f);
            Assert.That(math.length(controller.Current.c3.xyz - beforeCorrection), Is.LessThan(0.05));
        }

        [Test]
        public void Compensation_LargeOffset_NeverInflatesResidualIntoACorrection()
        {
            var controller = new DriftCorrectionController();
            controller.Set(double4x4.identity, double3.zero, 0f);

            // 0.85 (15% bias) drives a large offset; the estimate stays held on the base so any correction
            // would have to come from the offset — which the residual must never see.
            for (var i = 1; i <= 20; i++)
            {
                var corrected = controller.Observe(double4x4.identity, new double3(i, 0, 0), quaternion.identity, 0.85, i);
                Assert.That(corrected, Is.False, $"offset must not trigger a correction (observation {i})");
            }

            controller.Advance(1f);
            Assert.That(math.abs(controller.Current.c3.x), Is.GreaterThan(0.5), "offset should be substantial");
            Assert.That(math.abs(controller.Current.c3.x), Is.LessThanOrEqualTo(RelocalizationConfig.CompMaxOffsetMeters + Tolerance));
        }

        [Test]
        public void Set_IsInstantaneousAndConsistent()
        {
            var controller = new DriftCorrectionController();
            var target = Double4x4.FromTranslationRotation(new double3(7, 8, 9), quaternion.identity);

            controller.Set(target, double3.zero, 0f);

            AssertMatricesEqual(controller.Current, target);
            AssertMatricesEqual(math.mul(controller.Current, controller.CurrentInverse), double4x4.identity);
        }

        [Test]
        public void Observe_WithinDeadband_DoesNotTriggerOrMove()
        {
            var controller = new DriftCorrectionController();
            controller.Set(double4x4.identity, double3.zero, 0f);

            // 0.5 m of divergence sits inside the widest translation bar, so nothing is armed.
            var triggered = controller.Observe(Translation(0.5), double3.zero, quaternion.identity, null, 0f);

            Assert.That(triggered, Is.False);
            Assert.That(controller.Advance(1f), Is.False);
            AssertNearIdentity(controller.Current);
        }

        [Test]
        public void Observe_BeyondDeadband_ArmsSlewThatEasesToTarget()
        {
            var controller = new DriftCorrectionController();
            controller.Set(double4x4.identity, double3.zero, 0f);

            var triggered = controller.Observe(Translation(2), double3.zero, quaternion.identity, null, 0f);

            // Observe only arms the correction; the frame has not moved yet.
            Assert.That(triggered, Is.True);
            AssertNearIdentity(controller.Current);

            // A full slew duration lands exactly on the estimate.
            Assert.That(controller.Advance(RelocalizationConfig.CorrectionSlewSeconds), Is.True);
            Assert.That(controller.Current.c3.x, Is.EqualTo(2.0).Within(1e-6));
            AssertMatricesEqual(math.mul(controller.Current, controller.CurrentInverse), double4x4.identity);
        }

        [Test]
        public void Advance_MovesGraduallyNeverSnaps()
        {
            var controller = new DriftCorrectionController();
            controller.Set(double4x4.identity, double3.zero, 0f);
            controller.Observe(Translation(2), double3.zero, quaternion.identity, null, 0f);

            // A fraction of the slew duration moves the frame only part of the way — a slew, not a snap.
            controller.Advance(RelocalizationConfig.CorrectionSlewSeconds * 0.2f);

            Assert.That(controller.Current.c3.x, Is.GreaterThan(0.0));
            Assert.That(controller.Current.c3.x, Is.LessThan(2.0));
        }

        [Test]
        public void Threshold_DecaysWithDistance_AllowsSmallerCorrection()
        {
            // Fresh, a 0.3 m divergence is inside the widest deadband and does not trip a correction.
            var still = new DriftCorrectionController();
            still.Set(double4x4.identity, double3.zero, 0f);
            Assert.That(still.Observe(Translation(0.3), double3.zero, quaternion.identity, null, 0f), Is.False);

            // Walking far enough collapses the translation bar to its floor, so the same 0.3 m
            // divergence now trips a correction.
            var walked = new DriftCorrectionController();
            walked.Set(double4x4.identity, double3.zero, 0f);
            walked.Observe(double4x4.identity, double3.zero, quaternion.identity, null, 0f);
            var farVio = new double3(RelocalizationConfig.CorrectionDistanceToMinMeters * 2.0, 0, 0);

            Assert.That(walked.Observe(Translation(0.3), farVio, quaternion.identity, null, 0f), Is.True);
        }
    }
}
