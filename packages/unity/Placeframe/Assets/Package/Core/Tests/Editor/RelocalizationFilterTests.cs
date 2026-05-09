using System.Collections.Generic;
using MathNet.Numerics.LinearAlgebra;
using NUnit.Framework;
using PlaceframeApiClient.Model;
using Unity.Mathematics;

namespace Placeframe.Core.Tests
{
    public class RelocalizationFilterTests
    {
        [Test]
        public void InitialState_HasIdentityAlignmentAndUnflaggedHistory()
        {
            var state = RelocalizationFilter.InitialState();

            AssertNearIdentity(state.AlignmentMean);
            AssertNearIdentity(state.AlignmentCurrent);
            AssertNearIdentity(state.AlignmentCurrentInverse);
            Assert.That(state.HasAcceptedMeasurement, Is.False);
            Assert.That(state.LastAcceptedVioPosition, Is.Null);
            Assert.That(state.SlewProgress, Is.EqualTo(1f));
        }

        [Test]
        public void BootstrapCovariance_IsDiagonalWithExpectedVariances()
        {
            var sigma = RelocalizationFilter.BootstrapCovariance();
            var rotVar = RelocalizationFilter.BootstrapSigmaRotationRadians * RelocalizationFilter.BootstrapSigmaRotationRadians;
            var transVar =
                RelocalizationFilter.BootstrapSigmaTranslationMeters * RelocalizationFilter.BootstrapSigmaTranslationMeters;

            for (int r = 0; r < 6; r++)
            for (int c = 0; c < 6; c++)
            {
                var expected = r != c ? 0.0 : (r < 3 ? rotVar : transVar);
                Assert.That(sigma[r, c], Is.EqualTo(expected).Within(1e-9), $"sigma[{r},{c}]");
            }
        }

        [Test]
        public void SmoothStep_AtBoundaries_ReturnsBoundaryValues()
        {
            Assert.That(RelocalizationFilter.SmoothStep(0f), Is.EqualTo(0f).Within(1e-7));
            Assert.That(RelocalizationFilter.SmoothStep(1f), Is.EqualTo(1f).Within(1e-7));
            Assert.That(RelocalizationFilter.SmoothStep(0.5f), Is.EqualTo(0.5f).Within(1e-7));
        }

        [Test]
        public void ProcessNoise_NoPriorVioPosition_ReturnsBaseTerm()
        {
            var noise = RelocalizationFilter.ProcessNoise(new double3(1, 2, 3), null);

            var expected = new[]
            {
                RelocalizationFilter.BaseProcessNoiseRotationVariancePerTick,
                RelocalizationFilter.BaseProcessNoiseRotationVariancePerTick,
                RelocalizationFilter.BaseProcessNoiseRotationVariancePerTick,
                RelocalizationFilter.BaseProcessNoiseTranslationVariancePerTick,
                RelocalizationFilter.BaseProcessNoiseTranslationVariancePerTick,
                RelocalizationFilter.BaseProcessNoiseTranslationVariancePerTick,
            };
            for (int r = 0; r < 6; r++)
                for (int c = 0; c < 6; c++)
                    Assert.That(noise[r, c], Is.EqualTo(r == c ? expected[r] : 0.0).Within(1e-12));
        }

        [Test]
        public void ProcessNoise_MotionTermScalesQuadraticallyWithDistance()
        {
            var origin = new double3(0, 0, 0);
            var oneMeter = new double3(1, 0, 0);
            var twoMeters = new double3(2, 0, 0);

            var motionAtOne =
                RelocalizationFilter.ProcessNoise(oneMeter, origin)[0, 0]
                - RelocalizationFilter.BaseProcessNoiseRotationVariancePerTick;
            var motionAtTwo =
                RelocalizationFilter.ProcessNoise(twoMeters, origin)[0, 0]
                - RelocalizationFilter.BaseProcessNoiseRotationVariancePerTick;

            // Variance scales with σ², σ scales linearly with distance, so variance ∝ distance².
            Assert.That(motionAtTwo / motionAtOne, Is.EqualTo(4.0).Within(1e-9));
        }

        [Test]
        public void BuildCovarianceMatrix_CopiesElementsInOrder()
        {
            var covariance = new List<List<double>>
            {
                new List<double> { 1, 2, 3, 4, 5, 6 },
                new List<double> { 7, 8, 9, 10, 11, 12 },
                new List<double> { 13, 14, 15, 16, 17, 18 },
                new List<double> { 19, 20, 21, 22, 23, 24 },
                new List<double> { 25, 26, 27, 28, 29, 30 },
                new List<double> { 31, 32, 33, 34, 35, 36 },
            };

            var sigma = RelocalizationFilter.BuildCovarianceMatrix(covariance);

            for (int r = 0; r < 6; r++)
                for (int c = 0; c < 6; c++)
                    Assert.That(sigma[r, c], Is.EqualTo(covariance[r][c]));
        }

        [Test]
        public void MahalanobisSquared_IdentityCovariance_EqualsResidualNormSquared()
        {
            var residual = Vector<double>.Build.DenseOfArray(new[] { 1.0, 2.0, 3.0, 0.0, 0.0, 0.0 });
            var sigma = Matrix<double>.Build.DenseIdentity(6);

            var m2 = RelocalizationFilter.MahalanobisSquared(residual, sigma);

            Assert.That(m2, Is.EqualTo(14.0).Within(1e-9));
        }

        [Test]
        public void SummariseCovariance_ExtractsTranslationAndRotationStds()
        {
            var sigma = Matrix<double>.Build.DenseOfDiagonalArray(new[] { 1.0, 1.0, 1.0, 4.0, 4.0, 4.0 });

            var summary = RelocalizationFilter.SummariseCovariance(sigma);

            Assert.That(summary.TranslationStdMeters, Is.EqualTo(math.sqrt(12.0)).Within(1e-5));
            // sqrt(3) radians ≈ 99.22 degrees.
            Assert.That(summary.RotationStdDegrees, Is.EqualTo(math.degrees(math.sqrt(3.0))).Within(1e-3));
        }

        [Test]
        public void TickSlew_SettledState_IsNoOp()
        {
            var state = RelocalizationFilter.InitialState();

            var result = RelocalizationFilter.TickSlew(state, 0.1f);

            Assert.That(result.TransformChanged, Is.False);
            Assert.That(result.NewState.SlewProgress, Is.EqualTo(state.SlewProgress));
        }

        [Test]
        public void TickSlew_AdvancesProgressByDeltaOverDuration()
        {
            var state = RelocalizationFilter.InitialState();
            state.SlewProgress = 0f;
            state.SlewStart = double4x4.identity;
            state.AlignmentMean = double4x4.identity;
            state.AlignmentCurrent = double4x4.identity;

            var result = RelocalizationFilter.TickSlew(state, RelocalizationFilter.SlewDurationSeconds * 0.25f);

            Assert.That(result.NewState.SlewProgress, Is.EqualTo(0.25f).Within(1e-6));
            Assert.That(result.TransformChanged, Is.True);
        }

        [Test]
        public void TickSlew_OvershootDeltaClampsToOne()
        {
            var state = RelocalizationFilter.InitialState();
            state.SlewProgress = 0.9f;
            state.SlewStart = double4x4.identity;
            state.AlignmentMean = double4x4.identity;
            state.AlignmentCurrent = double4x4.identity;

            var result = RelocalizationFilter.TickSlew(state, RelocalizationFilter.SlewDurationSeconds);

            Assert.That(result.NewState.SlewProgress, Is.EqualTo(1f).Within(1e-6));
        }

        [Test]
        public void Reset_ReplacesAlignmentAndClearsHistory()
        {
            var state = RelocalizationFilter.InitialState();
            state.HasAcceptedMeasurement = true;
            state.LastAcceptedVioPosition = new double3(5, 5, 5);
            var newAlignment = Double4x4.FromTranslationRotation(new double3(1, 2, 3), quaternion.identity);

            var result = RelocalizationFilter.Reset(state, newAlignment);

            Assert.That(result.NewState.AlignmentMean.c3.x, Is.EqualTo(1.0).Within(1e-9));
            Assert.That(result.NewState.AlignmentMean.c3.y, Is.EqualTo(2.0).Within(1e-9));
            Assert.That(result.NewState.AlignmentMean.c3.z, Is.EqualTo(3.0).Within(1e-9));
            Assert.That(result.NewState.HasAcceptedMeasurement, Is.False);
            Assert.That(result.NewState.LastAcceptedVioPosition, Is.Null);
            Assert.That(result.TransformChanged, Is.True);
        }

        [Test]
        public void KalmanUpdate_ZeroResidual_PreservesMean()
        {
            var mean = double4x4.identity;
            var sigmaPredicted = Matrix<double>.Build.DenseIdentity(6);
            var residual = Vector<double>.Build.Dense(6);
            var innovationCov = Matrix<double>.Build.DenseIdentity(6) * 2.0;

            var posterior = RelocalizationFilter.KalmanUpdate(mean, sigmaPredicted, residual, innovationCov);

            // Mean unchanged when residual is zero.
            for (int c = 0; c < 4; c++)
                for (int r = 0; r < 4; r++)
                    Assert.That(posterior.NewMean[c][r], Is.EqualTo(mean[c][r]).Within(1e-9));
            // Posterior covariance shrinks: I - K = I - 0.5I = 0.5I, applied to sigmaPredicted = I → 0.5I.
            for (int r = 0; r < 6; r++)
                for (int c = 0; c < 6; c++)
                {
                    var expected = r == c ? 0.5 : 0.0;
                    Assert.That(posterior.NewCovariance[r, c], Is.EqualTo(expected).Within(1e-9));
                }
        }

        [Test]
        public void ApplyMeasurement_BelowConfidenceFloor_RejectsAndPreservesState()
        {
            var state = RelocalizationFilter.InitialState();
            var measurement = MakeMapLocalization(
                tightConfidence: 0.5,
                looseConfidence: RelocalizationFilter.LooseLowerBound - 0.01
            );
            var frame = new CameraFrame { CameraTranslationUnityWorldFromCamera = float3.zero };

            var result = RelocalizationFilter.ApplyMeasurement(state, measurement, frame);

            Assert.That(result.Rejection, Is.EqualTo(MeasurementRejection.ConfidenceFloor));
            Assert.That(result.TransformChanged, Is.False);
            Assert.That(result.NewState.HasAcceptedMeasurement, Is.False);
        }

        [Test]
        public void ApplyMeasurement_FirstAcceptAlwaysSnaps()
        {
            var state = RelocalizationFilter.InitialState();
            var measurement = MakeMapLocalization(tightConfidence: 0.99, looseConfidence: 0.99);
            var frame = new CameraFrame
            {
                CameraTranslationUnityWorldFromCamera = float3.zero,
                CameraRotationUnityWorldFromCamera = quaternion.identity,
            };

            var result = RelocalizationFilter.ApplyMeasurement(state, measurement, frame);

            Assert.That(result.Rejection, Is.EqualTo(MeasurementRejection.None));
            Assert.That(result.TransformChanged, Is.True);
            Assert.That(result.NewState.HasAcceptedMeasurement, Is.True);
            Assert.That(result.NewState.SlewProgress, Is.EqualTo(1f));
        }

        [Test]
        public void ShiftMagnitudeSquared_SamePose_IsZero()
        {
            var pose = double4x4.identity;
            var sigma = Matrix<double>.Build.DenseIdentity(6);

            var shift = RelocalizationFilter.ShiftMagnitudeSquared(pose, pose, sigma);

            Assert.That(shift, Is.EqualTo(0.0).Within(1e-9));
        }

        private static MapLocalization MakeMapLocalization(double tightConfidence, double looseConfidence)
        {
            var identityCov = new List<List<double>>();
            for (int r = 0; r < 6; r++)
            {
                var row = new List<double>();
                for (int c = 0; c < 6; c++)
                    row.Add(r == c ? 1.0 : 0.0);
                identityCov.Add(row);
            }
            var metrics = new LocalizationMetrics(
                inlierRatio: 0.9,
                reprojectionErrorMedian: 0.5,
                numInliers: 100,
                numCorrespondences: 110,
                numMatches: 120,
                inlierCoverage: 0.8,
                confidenceTight: tightConfidence,
                confidenceLoose: looseConfidence,
                confidenceIsCalibrated: true,
                measurementCovariance: identityCov,
                pnpCovariance: identityCov,
                pipelineVersion: "test"
            );
            var identityTransform = new Transform(
                translation: new Float3(0, 0, 0),
                rotation: new Float4(0, 0, 0, 1)
            );
            return new MapLocalization(
                id: System.Guid.NewGuid(),
                cameraFromMapTransform: identityTransform,
                mapTransform: identityTransform,
                metrics: metrics
            );
        }

        private static void AssertNearIdentity(double4x4 m)
        {
            for (int c = 0; c < 4; c++)
                for (int r = 0; r < 4; r++)
                {
                    var expected = c == r ? 1.0 : 0.0;
                    Assert.That(m[c][r], Is.EqualTo(expected).Within(1e-9), $"m[{c}][{r}]");
                }
        }
    }
}
