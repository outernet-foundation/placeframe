using NUnit.Framework;
using PlaceframeApiClient.Model;
using Unity.Mathematics;
using static Placeframe.Core.Tests.RelocalizationTestHelpers;

namespace Placeframe.Core.Tests
{
    public class MultiHypothesisFilterTests
    {
        private static MultiHypothesisFilter NewFilter() => new MultiHypothesisFilter();

        [Test]
        public void Bootstrap_FirstMeasurement_BecomesBestEstimate()
        {
            var filter = NewFilter();

            var outcome = Apply(filter, alignmentX: 5, cameraX: 0, 0f);

            Assert.That(outcome, Is.EqualTo(MeasurementOutcome.Bootstrapped));
            Assert.That(filter.HypothesisCount, Is.EqualTo(1));
            Assert.That(filter.BestEstimate.c3.x, Is.EqualTo(5.0).Within(1e-6));
        }

        [Test]
        public void QualityGate_RejectsLowQualityMeasurement()
        {
            var filter = NewFilter();

            var outcome = Apply(filter, alignmentX: 0, cameraX: 0, 0f, inlierRatio: 0.1);

            Assert.That(outcome, Is.EqualTo(MeasurementOutcome.Rejected));
            Assert.That(filter.HypothesisCount, Is.EqualTo(0));
        }

        [Test]
        public void FarMeasurement_SpawnsHypothesis_LeaderUnchanged()
        {
            var filter = NewFilter();
            Apply(filter, alignmentX: 0, cameraX: 0, 0f);

            var outcome = Apply(filter, alignmentX: 25, cameraX: 0, 1f);

            Assert.That(outcome, Is.EqualTo(MeasurementOutcome.Accepted));
            Assert.That(filter.HypothesisCount, Is.EqualTo(2));
            Assert.That(filter.PublishedHypothesisId, Is.EqualTo(0));
            Assert.That(filter.BestEstimate.c3.x, Is.EqualTo(0.0).Within(1e-6));
        }

        [Test]
        public void NearMeasurement_MatchesLeader_NoSpawn()
        {
            var filter = NewFilter();
            Apply(filter, alignmentX: 0, cameraX: 0, 0f);

            var outcome = Apply(filter, alignmentX: 0.1, cameraX: 0, 1f);

            // No new hypothesis spawned: the near measurement folded into the existing leader, which
            // absorbed it as its new estimate.
            Assert.That(outcome, Is.EqualTo(MeasurementOutcome.Accepted));
            Assert.That(filter.HypothesisCount, Is.EqualTo(1));
            Assert.That(filter.PublishedHypothesisId, Is.EqualTo(0));
            Assert.That(filter.BestEstimate.c3.x, Is.EqualTo(0.1).Within(1e-6));
        }

        [Test]
        public void StaleHypothesis_DecaysAndIsPruned()
        {
            var filter = NewFilter();
            Apply(filter, alignmentX: 0, cameraX: 0, 0f);
            Apply(filter, alignmentX: 25, cameraX: 0, 1f);
            Assert.That(filter.HypothesisCount, Is.EqualTo(2));

            // Confirm the leader repeatedly from the same spot; the unsupported challenger decays from
            // its seed below the floor and is pruned.
            for (var i = 0; i < 50; i++)
            {
                Apply(filter, alignmentX: 0, cameraX: 0, 2f + i);
            }

            Assert.That(filter.HypothesisCount, Is.EqualTo(1));
            Assert.That(filter.PublishedHypothesisId, Is.EqualTo(0));
        }

        [Test]
        public void Bank_CapsAtMaxHypotheses()
        {
            var filter = NewFilter();
            Apply(filter, alignmentX: 0, cameraX: 0, 0f);

            for (var i = 1; i <= RelocalizationConfig.MaxHypotheses + 2; i++)
            {
                Apply(filter, alignmentX: 25.0 * i, cameraX: 0, i);
            }

            Assert.That(filter.HypothesisCount, Is.LessThanOrEqualTo(RelocalizationConfig.MaxHypotheses));
        }

        [Test]
        public void Reset_DropsAllHypothesesAndRebootstraps()
        {
            var filter = NewFilter();
            Apply(filter, alignmentX: 0, cameraX: 0, 0f);
            Apply(filter, alignmentX: 25, cameraX: 0, 1f);

            filter.Reset();

            Assert.That(filter.HypothesisCount, Is.EqualTo(0));
            Assert.That(filter.HasLeader, Is.False);

            var outcome = Apply(filter, alignmentX: 3, cameraX: 0, 2f);
            Assert.That(outcome, Is.EqualTo(MeasurementOutcome.Bootstrapped));
            Assert.That(filter.HypothesisCount, Is.EqualTo(1));
            Assert.That(filter.BestEstimate.c3.x, Is.EqualTo(3.0).Within(1e-6));
        }

        [Test]
        public void Promotion_RequiresMarginThenDwell()
        {
            var filter = NewFilter();
            Apply(filter, alignmentX: 0, cameraX: 0, 0f);
            Apply(filter, alignmentX: 25, cameraX: 0, 1f);

            // Confirm the challenger across motion: its alignment stays at 25 while the camera walks, so
            // it earns distance-weighted score while the unsupported leader decays. The referee runs on
            // each accepted measurement: the first that clears the margin starts the dwell, and a later
            // one — only once the dwell has elapsed — completes the handoff.
            Apply(filter, alignmentX: 25, cameraX: 2, 2f);
            Apply(filter, alignmentX: 25, cameraX: 4, 3f);

            // Margin cleared but dwell not yet elapsed: the original leader still leads.
            Assert.That(filter.PublishedHypothesisId, Is.EqualTo(0));

            // A measurement past the dwell completes the promotion.
            Apply(filter, alignmentX: 25, cameraX: 6, 4f);
            Assert.That(filter.PublishedHypothesisId, Is.EqualTo(1));
            Assert.That(filter.BestEstimate.c3.x, Is.EqualTo(25.0).Within(1e-6));
        }

        [Test]
        public void AbAliasing_BestEstimateNeverLeavesRegionA()
        {
            var filter = NewFilter();
            Apply(filter, alignmentX: 0, cameraX: 0, 0f);

            // The device lingers at the aliased spot: region B (25m away) is returned again and again
            // from essentially the same viewpoint while region A is not seen. B is confirmed far more
            // often than A ever was, but every B confirmation is stationary, so B earns no score and
            // can never clear the promotion margin — the belief stays anchored in region A.
            var now = 0f;
            for (var i = 0; i < 30; i++)
            {
                now += 0.1f;
                Apply(filter, alignmentX: 25, cameraX: 0, now);
            }

            Assert.That(filter.PublishedHypothesisId, Is.EqualTo(0));
            Assert.That(filter.BestEstimate.c3.x, Is.EqualTo(0.0).Within(1e-6));
            Assert.That(filter.HypothesisCount, Is.GreaterThanOrEqualTo(2));
        }

        [Test]
        public void Bootstrap_CameraAnchored_PlacesCameraExactlyAtVioPosition()
        {
            // Camera sits 10m east of the Unity world origin; ECEF map origin lands 5m north of the
            // camera (via cameraFromMap with translation [0, 0, 5] in OpenCV-y-down, which the basis
            // change to Unity flips). Bootstrap takes the measurement as the best estimate, and it must
            // satisfy unityCamera == estimate * ecefCamera, regardless of rotation noise.
            var frame = MakeFrame(new float3(10f, 0f, 0f));
            var cameraFromMap = new Transform(translation: new Float3(0, 0, 5), rotation: new Float4(0, 0, 0, 1));
            var mapTransform = new Transform(translation: new Float3(100, 200, 300), rotation: new Float4(0, 0, 0, 1));
            var localization = new MapLocalization(
                id: System.Guid.NewGuid(),
                cameraFromMapTransform: cameraFromMap,
                mapTransform: mapTransform,
                metrics: MakeMetrics()
            );

            var filter = NewFilter();
            filter.ApplyMeasurement(localization, frame, 0f);
            var alignment = filter.BestEstimate;

            var translationMapFromCamera = new double3(0, 0, -5);
            var (translationEcefFromMap, _) = LocationUtilities.ChangeBasisUnityFromEcef(new double3(100, 200, 300), double3x3.identity);
            var translationEcefFromCamera = translationMapFromCamera + translationEcefFromMap;

            var transformedCamera = math.transform(alignment, translationEcefFromCamera);
            Assert.That(transformedCamera.x, Is.EqualTo(10.0).Within(1e-6));
            Assert.That(transformedCamera.y, Is.EqualTo(0.0).Within(1e-6));
            Assert.That(transformedCamera.z, Is.EqualTo(0.0).Within(1e-6));
        }
    }

    public class DriftCorrectionControllerTests
    {
        private static double4x4 Translation(double x) =>
            Double4x4.FromTranslationRotation(new double3(x, 0, 0), quaternion.identity);

        [Test]
        public void Set_IsInstantaneousAndConsistent()
        {
            var controller = new DriftCorrectionController();
            var target = Double4x4.FromTranslationRotation(new double3(7, 8, 9), quaternion.identity);

            controller.Set(target, 0f);

            AssertMatricesEqual(controller.Current, target);
            AssertMatricesEqual(math.mul(controller.Current, controller.CurrentInverse), double4x4.identity);
        }

        [Test]
        public void Observe_WithinDeadband_DoesNotTriggerOrMove()
        {
            var controller = new DriftCorrectionController();
            controller.Set(double4x4.identity, 0f);

            // 0.5 m of divergence sits inside the widest translation bar, so nothing is armed.
            var triggered = controller.Observe(Translation(0.5), double3.zero, quaternion.identity, 0f);

            Assert.That(triggered, Is.False);
            Assert.That(controller.Advance(1f), Is.False);
            AssertNearIdentity(controller.Current);
        }

        [Test]
        public void Observe_BeyondDeadband_ArmsSlewThatEasesToTarget()
        {
            var controller = new DriftCorrectionController();
            controller.Set(double4x4.identity, 0f);

            var triggered = controller.Observe(Translation(2), double3.zero, quaternion.identity, 0f);

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
            controller.Set(double4x4.identity, 0f);
            controller.Observe(Translation(2), double3.zero, quaternion.identity, 0f);

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
            still.Set(double4x4.identity, 0f);
            Assert.That(still.Observe(Translation(0.3), double3.zero, quaternion.identity, 0f), Is.False);

            // Walking far enough collapses the translation bar to its floor, so the same 0.3 m
            // divergence now trips a correction.
            var walked = new DriftCorrectionController();
            walked.Set(double4x4.identity, 0f);
            walked.Observe(double4x4.identity, double3.zero, quaternion.identity, 0f);
            var farVio = new double3(RelocalizationConfig.CorrectionDistanceToMinMeters * 2.0, 0, 0);

            Assert.That(walked.Observe(Translation(0.3), farVio, quaternion.identity, 0f), Is.True);
        }
    }
}
