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
            var transVar = RelocalizationFilter.BootstrapSigmaTranslationMeters * RelocalizationFilter.BootstrapSigmaTranslationMeters;

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

            var motionAtOne = RelocalizationFilter.ProcessNoise(oneMeter, origin)[0, 0] - RelocalizationFilter.BaseProcessNoiseRotationVariancePerTick;
            var motionAtTwo = RelocalizationFilter.ProcessNoise(twoMeters, origin)[0, 0] - RelocalizationFilter.BaseProcessNoiseRotationVariancePerTick;

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
        public void ApplyMeasurement_FirstAcceptAlwaysSnaps()
        {
            var state = RelocalizationFilter.InitialState();
            var measurement = MakeMapLocalization(tightConfidence: 0.99, looseConfidence: 0.99);
            var frame = new CameraFrame { CameraTranslationUnityWorldFromCamera = float3.zero, CameraRotationUnityWorldFromCamera = quaternion.identity };

            var result = RelocalizationFilter.ApplyMeasurement(state, measurement, frame);

            Assert.That(result.Rejection, Is.EqualTo(MeasurementRejection.None));
            Assert.That(result.TransformChanged, Is.True);
            Assert.That(result.NewState.HasAcceptedMeasurement, Is.True);
            Assert.That(result.NewState.SlewProgress, Is.EqualTo(1f));
        }

        [Test]
        public void ApplyMeasurement_RejectionInflatesStoredCovariance()
        {
            var origin = new CameraFrame { CameraTranslationUnityWorldFromCamera = float3.zero, CameraRotationUnityWorldFromCamera = quaternion.identity };
            var accepted = RelocalizationFilter
                .ApplyMeasurement(RelocalizationFilter.InitialState(), MakeMapLocalization(tightConfidence: 0.99, looseConfidence: 0.99), origin)
                .NewState;
            var sigmaAfterAccept = accepted.AlignmentCovariance;

            // 10 m residual against σ_meas = I_6 yields m² ≈ 100 — well above the 16.81 gate.
            var jumped = new CameraFrame
            {
                CameraTranslationUnityWorldFromCamera = new float3(10f, 0f, 0f),
                CameraRotationUnityWorldFromCamera = quaternion.identity,
            };
            var rejected = RelocalizationFilter.ApplyMeasurement(accepted, MakeMapLocalization(tightConfidence: 0.99, looseConfidence: 0.99), jumped);

            Assert.That(rejected.Rejection, Is.EqualTo(MeasurementRejection.InnovationGate));
            // Motion noise (0.01·10)² = 1e-2 dwarfs the 1e-4 per-tick base term.
            for (int i = 3; i < 6; i++)
                Assert.That(
                    rejected.NewState.AlignmentCovariance[i, i],
                    Is.GreaterThan(sigmaAfterAccept[i, i] + 9e-3),
                    $"diag[{i}] did not absorb motion-proportional process noise"
                );
        }

        [Test]
        public void ApplyMeasurement_RejectionRecoversAfterRepeatedJumpMeasurements()
        {
            var measurement = MakeMapLocalization(tightConfidence: 0.99, looseConfidence: 0.99);
            var state = RelocalizationFilter
                .ApplyMeasurement(
                    RelocalizationFilter.InitialState(),
                    measurement,
                    new CameraFrame { CameraTranslationUnityWorldFromCamera = float3.zero, CameraRotationUnityWorldFromCamera = quaternion.identity }
                )
                .NewState;
            var jumpedFrame = new CameraFrame
            {
                CameraTranslationUnityWorldFromCamera = new float3(10f, 0f, 0f),
                CameraRotationUnityWorldFromCamera = quaternion.identity,
            };

            var recovered = false;
            for (int tick = 0; tick < 600; tick++)
            {
                var step = RelocalizationFilter.ApplyMeasurement(state, measurement, jumpedFrame);
                state = step.NewState;
                if (step.Rejection == MeasurementRejection.None)
                {
                    recovered = true;
                    break;
                }
            }

            Assert.That(recovered, Is.True, "filter never re-accepted after a sustained VIO jump");
        }

        [Test]
        public void ApplyMeasurement_RejectionCapsCovarianceAtBootstrap()
        {
            var bootstrap = RelocalizationFilter.BootstrapCovariance();
            var oversized = bootstrap.Clone();
            for (int i = 0; i < 6; i++)
                oversized[i, i] = bootstrap[i, i] * 10.0;
            var state = RelocalizationFilter.InitialState();
            state.HasAcceptedMeasurement = true;
            state.LastAcceptedVioPosition = new double3(0, 0, 0);
            state.AlignmentCovariance = oversized;
            // Residual must dwarf the inflated innovation covariance for the gate to fire.
            var jumped = new CameraFrame
            {
                CameraTranslationUnityWorldFromCamera = new float3(2000f, 0f, 0f),
                CameraRotationUnityWorldFromCamera = quaternion.identity,
            };

            var result = RelocalizationFilter.ApplyMeasurement(state, MakeMapLocalization(tightConfidence: 0.99, looseConfidence: 0.99), jumped);

            Assert.That(result.Rejection, Is.EqualTo(MeasurementRejection.InnovationGate));
            for (int i = 0; i < 6; i++)
                Assert.That(result.NewState.AlignmentCovariance[i, i], Is.LessThanOrEqualTo(bootstrap[i, i] + 1e-9), $"diag[{i}] exceeded bootstrap cap");
        }

        [Test]
        public void ShiftMagnitudeSquared_SamePose_IsZero()
        {
            var pose = double4x4.identity;
            var sigma = Matrix<double>.Build.DenseIdentity(6);

            var shift = RelocalizationFilter.ShiftMagnitudeSquared(pose, pose, sigma);

            Assert.That(shift, Is.EqualTo(0.0).Within(1e-9));
        }

        [Test]
        public void ComputeAlignmentFromResult_CameraAnchored_PlacesCameraExactlyAtVioPosition()
        {
            // Camera sits 10m east of the Unity world origin; ECEF map origin lands 5m north of the
            // camera (via cameraFromMap with translation [0, 0, 5] in OpenCV-y-down, which the
            // basis change to Unity flips). The published alignment must satisfy
            // unityCamera == AlignmentMean * ecefCamera, regardless of the rotation noise.
            var frame = new CameraFrame
            {
                CameraTranslationUnityWorldFromCamera = new float3(10f, 0f, 0f),
                CameraRotationUnityWorldFromCamera = quaternion.identity,
            };
            var cameraFromMap = new Transform(translation: new Float3(0, 0, 5), rotation: new Float4(0, 0, 0, 1));
            var mapTransform = new Transform(translation: new Float3(100, 200, 300), rotation: new Float4(0, 0, 0, 1));
            var localization = new MapLocalization(
                id: System.Guid.NewGuid(),
                cameraFromMapTransform: cameraFromMap,
                mapTransform: mapTransform,
                metrics: BuildMetrics()
            );

            var measurement = RelocalizationFilter.ComputeAlignmentFromResult(localization, frame);
            var alignment = Double4x4.FromTranslationRotation(measurement.Translation, measurement.RotationUnityFromEcef);

            // Reconstruct the camera's ECEF position from the same inputs the measurement used:
            // map_to_camera = inverse(cameraFromMap), camera_in_ecef = mapTransform * map_to_camera.
            var translationMapFromCamera = new double3(0, 0, -5);
            // mapTransform is ECEF-from-map in Y-down; reproduce the Unity-basis ECEF camera location.
            var (translationEcefFromMap, _) = LocationUtilities.ChangeBasisUnityFromEcef(new double3(100, 200, 300), double3x3.identity);
            var translationEcefFromCamera = translationMapFromCamera + translationEcefFromMap;

            var transformedCamera = math.transform(alignment, translationEcefFromCamera);
            Assert.That(transformedCamera.x, Is.EqualTo(10.0).Within(1e-6));
            Assert.That(transformedCamera.y, Is.EqualTo(0.0).Within(1e-6));
            Assert.That(transformedCamera.z, Is.EqualTo(0.0).Within(1e-6));
        }

        [Test]
        public void ApplyMeasurement_BypassInnovationGate_AcceptsOutlier()
        {
            var measurement = MakeMapLocalization(tightConfidence: 0.99, looseConfidence: 0.99);
            var accepted = RelocalizationFilter
                .ApplyMeasurement(
                    RelocalizationFilter.InitialState(),
                    measurement,
                    new CameraFrame { CameraTranslationUnityWorldFromCamera = float3.zero, CameraRotationUnityWorldFromCamera = quaternion.identity }
                )
                .NewState;
            var jumped = new CameraFrame
            {
                CameraTranslationUnityWorldFromCamera = new float3(50f, 0f, 0f),
                CameraRotationUnityWorldFromCamera = quaternion.identity,
            };

            var rejected = RelocalizationFilter.ApplyMeasurement(accepted, measurement, jumped);
            Assert.That(rejected.Rejection, Is.EqualTo(MeasurementRejection.InnovationGate));

            var bypassed = RelocalizationFilter.ApplyMeasurement(accepted, measurement, jumped, new ApplyMeasurementOptions { BypassInnovationGate = true });
            Assert.That(bypassed.Rejection, Is.EqualTo(MeasurementRejection.None));
            Assert.That(bypassed.NewState.HasAcceptedMeasurement, Is.True);
        }

        [Test]
        public void ApplyMeasurement_BypassKalman_SnapsPosteriorToMeasurement()
        {
            var measurement = MakeMapLocalization(tightConfidence: 0.99, looseConfidence: 0.99);
            var frame = new CameraFrame { CameraTranslationUnityWorldFromCamera = float3.zero, CameraRotationUnityWorldFromCamera = quaternion.identity };
            var seeded = RelocalizationFilter.ApplyMeasurement(RelocalizationFilter.InitialState(), measurement, frame).NewState;

            // Without bypass, a second identical measurement gets Kalman-merged with the prior.
            // With bypass, the posterior snaps to the raw measurement and the covariance re-bootstraps.
            var result = RelocalizationFilter.ApplyMeasurement(seeded, measurement, frame, new ApplyMeasurementOptions { BypassKalman = true });

            Assert.That(result.Rejection, Is.EqualTo(MeasurementRejection.None));
            Assert.That(result.Snapped, Is.True);
            var bootstrap = RelocalizationFilter.BootstrapCovariance();
            for (int i = 0; i < 6; i++)
                Assert.That(result.NewState.AlignmentCovariance[i, i], Is.EqualTo(bootstrap[i, i]).Within(1e-9));
        }

        private static LocalizationMetrics BuildMetrics()
        {
            var identityCov = new List<List<double>>();
            for (int r = 0; r < 6; r++)
            {
                var row = new List<double>();
                for (int c = 0; c < 6; c++)
                    row.Add(r == c ? 1.0 : 0.0);
                identityCov.Add(row);
            }
            return new LocalizationMetrics(
                inlierRatio: 0.9,
                reprojectionErrorMedian: 0.5,
                numInliers: 100,
                numCorrespondences: 110,
                numMatches: 120,
                inlierCoverage: 0.8,
                confidenceTight: 0.99,
                confidenceLoose: 0.99,
                confidenceIsCalibrated: true,
                measurementCovariance: identityCov,
                pnpCovariance: identityCov,
                pipelineVersion: "test"
            );
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
            var identityTransform = new Transform(translation: new Float3(0, 0, 0), rotation: new Float4(0, 0, 0, 1));
            return new MapLocalization(id: System.Guid.NewGuid(), cameraFromMapTransform: identityTransform, mapTransform: identityTransform, metrics: metrics);
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
