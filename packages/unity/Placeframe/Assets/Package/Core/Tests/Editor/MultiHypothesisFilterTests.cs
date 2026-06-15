using NUnit.Framework;
using PlaceframeApiClient.Model;
using Unity.Mathematics;
using static Placeframe.Core.Tests.RelocalizationTestHelpers;

namespace Placeframe.Core.Tests
{
    public class MultiHypothesisFilterTests
    {
        private static MultiHypothesisFilter NewFilter() => new MultiHypothesisFilter();

        // One query carrying several clusters: each alignmentX publishes the world origin at that x while the
        // device (VIO) sits at cameraX, the same convention as the single-measurement Apply helper.
        private static MeasurementOutcome ApplyBatch(MultiHypothesisFilter filter, double cameraX, float nowSeconds, params double[] alignmentXs)
        {
            var camera = new float3((float)cameraX, 0f, 0f);
            var measurements = new MapLocalization[alignmentXs.Length];
            for (var i = 0; i < alignmentXs.Length; i++)
            {
                var mapTranslation = new float3((float)(cameraX - alignmentXs[i]), 0f, 0f);
                measurements[i] = MakeLocalization(mapTranslation: mapTranslation);
            }

            return filter.ApplyMeasurements(measurements, MakeFrame(camera), nowSeconds);
        }

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

        [Test]
        public void RecoversFromStaleLock_OnceCappedScoreDecays()
        {
            var filter = NewFilter();
            Apply(filter, alignmentX: 0, cameraX: 0, 0f);

            // Bank the leader hard across a long motion-rich stretch. Capped, its score saturates at
            // ScoreCap; uncapped it would accumulate without bound and become impossible to overtake.
            var now = 0f;
            for (var i = 1; i <= 20; i++)
            {
                now = i;
                Apply(filter, alignmentX: 0, cameraX: 5 * i, now);
            }

            Assert.That(filter.PublishedHypothesisId, Is.EqualTo(0));

            // Stop confirming the leader; confirm a distinct pose across continued motion. The leader decays
            // from the cap while the challenger climbs, so the lead changes hands within a bounded number of
            // queries — the behavior an unbounded score denied.
            for (var i = 1; i <= 10; i++)
            {
                now += 1;
                Apply(filter, alignmentX: 25, cameraX: 100 + 5 * i, now);
            }

            Assert.That(filter.PublishedHypothesisId, Is.EqualTo(1));
            Assert.That(filter.BestEstimate.c3.x, Is.EqualTo(25.0).Within(1e-6));
        }

        [Test]
        public void BatchDedup_TwoClustersSamePose_ConfirmOneHypothesis()
        {
            var filter = NewFilter();
            Apply(filter, alignmentX: 0, cameraX: 0, 0f);
            var before = filter.HypothesisCount;

            // A query whose two clusters solve to nearly the same far pose must confirm a single hypothesis:
            // the second falls inside the gate of the one the first just spawned and is dropped as redundant.
            ApplyBatch(filter, cameraX: 0, nowSeconds: 1f, 25.0, 25.05);

            Assert.That(filter.HypothesisCount, Is.EqualTo(before + 1));
        }

        [Test]
        public void Eviction_FreshlyConfirmedChallengerSurvivesCapacityChurn()
        {
            var filter = NewFilter();
            Apply(filter, alignmentX: 0, cameraX: 0, 0f);

            // Every query confirms the challenger across motion alongside a unique one-off pose, holding the
            // bank at capacity. The freshly-confirmed challenger is never the eviction target — the abandoned
            // one-off poses are — so it accumulates and takes the lead while the bank stays bounded.
            var now = 0f;
            for (var i = 1; i <= 12; i++)
            {
                now = i;
                ApplyBatch(filter, cameraX: 5.0 * i, nowSeconds: now, 25.0, 200.0 + (50.0 * i));
            }

            Assert.That(filter.HypothesisCount, Is.LessThanOrEqualTo(RelocalizationConfig.MaxHypotheses));
            Assert.That(filter.PublishedHypothesisId, Is.EqualTo(1));
            Assert.That(filter.BestEstimate.c3.x, Is.EqualTo(25.0).Within(1e-6));
        }

        [Test]
        public void Spawn_QualitySeedsSurvivalButNeverPromotesAlone()
        {
            var strong = NewFilter();
            Apply(strong, alignmentX: 0, cameraX: 0, 0f, inlierRatio: 0.9, numInliers: 100);
            // A far, much-stronger lock spawns as a non-leader; its seed must exceed a weak spawn's...
            Apply(strong, alignmentX: 25, cameraX: 0, 1f, inlierRatio: 0.9, numInliers: 3000);
            var strongOnlyHypotheses = strong.HypothesisCount;

            var weak = NewFilter();
            Apply(weak, alignmentX: 0, cameraX: 0, 0f, inlierRatio: 0.9, numInliers: 100);
            Apply(weak, alignmentX: 25, cameraX: 0, 1f, inlierRatio: 0.3, numInliers: 60);

            // ...yet a fresh strong spawn, never walked, must not seize the lead on its seed alone.
            Assert.That(strong.PublishedHypothesisId, Is.EqualTo(0));
            Assert.That(strong.BestEstimate.c3.x, Is.EqualTo(0.0).Within(1e-6));
            Assert.That(strongOnlyHypotheses, Is.EqualTo(2));

            // The strong spawn outlives the decay-and-prune window the weak one falls inside.
            for (var i = 0; i < 12; i++)
            {
                Apply(strong, alignmentX: 0, cameraX: 0, 2f + i, numInliers: 100);
                Apply(weak, alignmentX: 0, cameraX: 0, 2f + i, numInliers: 100);
            }

            Assert.That(strong.HypothesisCount, Is.EqualTo(2), "high-quality spawn survives the decay window");
            Assert.That(weak.HypothesisCount, Is.EqualTo(1), "low-quality spawn decays below the floor and is pruned");
        }

        [Test]
        public void QualityDominance_StrongChallengerPromotesEarlierThanMarginAlone()
        {
            // Same weak incumbent and same walk in both filters; only the challenger's quality differs.
            // Identical motion means the pure score-margin path would promote at the same query, so any
            // difference in outcome isolates the quality-dominance path.
            var dominant = NewFilter();
            var control = NewFilter();

            foreach (var filter in new[] { dominant, control })
            {
                Apply(filter, alignmentX: 0, cameraX: 0, 0f, inlierRatio: 0.48, numInliers: 600);
                Apply(filter, alignmentX: 0, cameraX: 2, 1f, inlierRatio: 0.48, numInliers: 600);
            }

            // A far lock appears and is confirmed across a walk — strongly out-evidencing the incumbent in
            // the dominant filter, merely equal-quality in the control.
            var camera = 4;
            for (var t = 2; t <= 5; t++)
            {
                Apply(dominant, alignmentX: 25, cameraX: camera, t, inlierRatio: 0.80, numInliers: 3000);
                Apply(control, alignmentX: 25, cameraX: camera, t, inlierRatio: 0.48, numInliers: 600);
                camera += 2;
            }

            // The dominant challenger established its lead two queries earlier — on quality, while still
            // below the score margin — so it clears the dwell and promotes; the control, established only
            // once the margin finally cleared, is still inside its dwell.
            Assert.That(dominant.PublishedHypothesisId, Is.EqualTo(1));
            Assert.That(dominant.BestEstimate.c3.x, Is.EqualTo(25.0).Within(1e-6));
            Assert.That(control.PublishedHypothesisId, Is.EqualTo(0));
        }

        [Test]
        public void QualityDominance_StrongChallengerWithoutMotion_DoesNotPromote()
        {
            var filter = NewFilter();
            Apply(filter, alignmentX: 0, cameraX: 0, 0f, inlierRatio: 0.48, numInliers: 600);

            // A much-stronger lock is re-confirmed many times, but always from the same spot (no motion),
            // so it is a single-viewpoint alias: the dominance path's motion requirement excludes it and the
            // belief stays anchored to the incumbent — the anti-aliasing core is preserved.
            var now = 0f;
            for (var i = 0; i < 30; i++)
            {
                now += 0.1f;
                Apply(filter, alignmentX: 25, cameraX: 0, now, inlierRatio: 0.85, numInliers: 3000);
            }

            Assert.That(filter.PublishedHypothesisId, Is.EqualTo(0));
            Assert.That(filter.BestEstimate.c3.x, Is.EqualTo(0.0).Within(1e-6));
        }
    }
}
