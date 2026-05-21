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
        public void InitialState_HasZeroAlignmentAndUnflaggedHistory()
        {
            var state = RelocalizationFilter.InitialState();

            Assert.That(state.Yaw, Is.EqualTo(0.0));
            Assert.That(state.Translation, Is.EqualTo(double3.zero));
            Assert.That(state.YawCurrent, Is.EqualTo(0.0));
            Assert.That(state.TranslationCurrent, Is.EqualTo(double3.zero));
            Assert.That(state.HasAcceptedMeasurement, Is.False);
            Assert.That(state.LastAcceptedVioPosition, Is.Null);
            Assert.That(state.SlewProgress, Is.EqualTo(1f));
        }

        [Test]
        public void BootstrapCovariance_IsDiagonalWithExpectedVariances()
        {
            var sigma = RelocalizationFilter.BootstrapCovariance();
            var yawVar = RelocalizationFilter.BootstrapSigmaYawRadians * RelocalizationFilter.BootstrapSigmaYawRadians;
            var transVar =
                RelocalizationFilter.BootstrapSigmaTranslationMeters * RelocalizationFilter.BootstrapSigmaTranslationMeters;

            var expected = new[] { yawVar, transVar, transVar, transVar };
            for (int r = 0; r < 4; r++)
                for (int c = 0; c < 4; c++)
                    Assert.That(sigma[r, c], Is.EqualTo(r == c ? expected[r] : 0.0).Within(1e-9), $"sigma[{r},{c}]");
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
                RelocalizationFilter.BaseProcessNoiseYawVariancePerTick,
                RelocalizationFilter.BaseProcessNoiseTranslationVariancePerTick,
                RelocalizationFilter.BaseProcessNoiseTranslationVariancePerTick,
                RelocalizationFilter.BaseProcessNoiseTranslationVariancePerTick,
            };
            for (int r = 0; r < 4; r++)
                for (int c = 0; c < 4; c++)
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
                - RelocalizationFilter.BaseProcessNoiseYawVariancePerTick;
            var motionAtTwo =
                RelocalizationFilter.ProcessNoise(twoMeters, origin)[0, 0]
                - RelocalizationFilter.BaseProcessNoiseYawVariancePerTick;

            Assert.That(motionAtTwo / motionAtOne, Is.EqualTo(4.0).Within(1e-9));
        }

        [Test]
        public void BuildCovarianceMatrix_CopiesElementsInOrder()
        {
            var covariance = new List<List<double>>();
            for (int r = 0; r < 6; r++)
            {
                var row = new List<double>();
                for (int c = 0; c < 6; c++)
                    row.Add(r * 6 + c + 1);
                covariance.Add(row);
            }

            var sigma = RelocalizationFilter.BuildCovarianceMatrix(covariance);

            for (int r = 0; r < 6; r++)
                for (int c = 0; c < 6; c++)
                    Assert.That(sigma[r, c], Is.EqualTo(covariance[r][c]));
        }

        [Test]
        public void ProjectCovariance_KeepsYawAndTranslationDimensions()
        {
            var sigma6 = Matrix<double>.Build.Dense(6, 6, (r, c) => r * 6 + c + 1);

            var sigma4 = RelocalizationFilter.ProjectCovariance(sigma6);

            var keep = new[] { 1, 3, 4, 5 };
            for (int i = 0; i < 4; i++)
                for (int j = 0; j < 4; j++)
                    Assert.That(sigma4[i, j], Is.EqualTo(sigma6[keep[i], keep[j]]));
        }

        [Test]
        public void MahalanobisSquared_IdentityCovariance_EqualsResidualNormSquared()
        {
            var residual = Vector<double>.Build.DenseOfArray(new[] { 1.0, 2.0, 3.0, 0.0 });
            var sigma = Matrix<double>.Build.DenseIdentity(4);

            var m2 = RelocalizationFilter.MahalanobisSquared(residual, sigma);

            Assert.That(m2, Is.EqualTo(14.0).Within(1e-9));
        }

        [Test]
        public void SummariseCovariance_ExtractsTranslationAndYawStds()
        {
            var sigma = Matrix<double>.Build.DenseOfDiagonalArray(new[] { 1.0, 4.0, 4.0, 4.0 });

            var summary = RelocalizationFilter.SummariseCovariance(sigma);

            Assert.That(summary.TranslationStdMeters, Is.EqualTo(math.sqrt(12.0)).Within(1e-5));
            Assert.That(summary.RotationStdDegrees, Is.EqualTo(math.degrees(1.0)).Within(1e-3));
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

            var result = RelocalizationFilter.TickSlew(state, RelocalizationFilter.SlewDurationSeconds * 0.25f);

            Assert.That(result.NewState.SlewProgress, Is.EqualTo(0.25f).Within(1e-6));
            Assert.That(result.TransformChanged, Is.True);
        }

        [Test]
        public void TickSlew_OvershootDeltaClampsToOne()
        {
            var state = RelocalizationFilter.InitialState();
            state.SlewProgress = 0.9f;

            var result = RelocalizationFilter.TickSlew(state, RelocalizationFilter.SlewDurationSeconds);

            Assert.That(result.NewState.SlewProgress, Is.EqualTo(1f).Within(1e-6));
        }

        [Test]
        public void TickSlew_YawTakesShortestArcAcrossPi()
        {
            var state = RelocalizationFilter.InitialState();
            state.YawSlewStart = math.PI_DBL - 0.1;
            state.Yaw = -math.PI_DBL + 0.1;
            state.SlewProgress = 0f;

            var result = RelocalizationFilter.TickSlew(state, RelocalizationFilter.SlewDurationSeconds * 0.5f);

            // Midpoint of the shortest arc across +π should land near ±π, not near 0.
            Assert.That(math.abs(MathUtil.WrapAngle(result.NewState.YawCurrent - math.PI_DBL)), Is.LessThan(0.1));
        }

        [Test]
        public void Reset_FromYawAndTranslation_ClearsHistory()
        {
            var state = RelocalizationFilter.InitialState();
            state.HasAcceptedMeasurement = true;
            state.LastAcceptedVioPosition = new double3(5, 5, 5);

            var result = RelocalizationFilter.Reset(state, 1.0, new double3(1, 2, 3));

            Assert.That(result.NewState.Yaw, Is.EqualTo(1.0).Within(1e-9));
            Assert.That(result.NewState.Translation, Is.EqualTo(new double3(1, 2, 3)));
            Assert.That(result.NewState.HasAcceptedMeasurement, Is.False);
            Assert.That(result.NewState.LastAcceptedVioPosition, Is.Null);
            Assert.That(result.TransformChanged, Is.True);
        }

        [Test]
        public void Reset_FromDouble4x4_ExtractsYawAndTranslation()
        {
            var yaw = math.radians(45.0);
            var translation = new double3(7, 8, 9);
            var alignment = RelocalizationFilter.BuildAlignment(yaw, translation);

            var result = RelocalizationFilter.Reset(RelocalizationFilter.InitialState(), alignment);

            Assert.That(result.NewState.Yaw, Is.EqualTo(yaw).Within(1e-6));
            Assert.That(result.NewState.Translation.x, Is.EqualTo(7.0).Within(1e-9));
            Assert.That(result.NewState.Translation.y, Is.EqualTo(8.0).Within(1e-9));
            Assert.That(result.NewState.Translation.z, Is.EqualTo(9.0).Within(1e-9));
        }

        [Test]
        public void KalmanUpdate_ZeroResidual_PreservesMean()
        {
            var sigmaPredicted = Matrix<double>.Build.DenseIdentity(4);
            var residual = Vector<double>.Build.Dense(4);
            var innovationCov = Matrix<double>.Build.DenseIdentity(4) * 2.0;

            var posterior = RelocalizationFilter.KalmanUpdate(
                0.5,
                new double3(1, 2, 3),
                sigmaPredicted,
                residual,
                innovationCov
            );

            Assert.That(posterior.NewYaw, Is.EqualTo(0.5).Within(1e-9));
            Assert.That(posterior.NewTranslation, Is.EqualTo(new double3(1, 2, 3)));
            for (int r = 0; r < 4; r++)
                for (int c = 0; c < 4; c++)
                {
                    var expected = r == c ? 0.5 : 0.0;
                    Assert.That(posterior.NewCovariance[r, c], Is.EqualTo(expected).Within(1e-9));
                }
        }

        [Test]
        public void ComputeInnovation_YawResidualWrapsAcrossPi()
        {
            var sigma = Matrix<double>.Build.DenseIdentity(4);

            var innov = RelocalizationFilter.ComputeInnovation(
                math.PI_DBL - 0.01,
                double3.zero,
                sigma,
                -math.PI_DBL + 0.01,
                double3.zero,
                sigma
            );

            Assert.That(innov.Residual[0], Is.EqualTo(0.02).Within(1e-9));
        }

        [Test]
        public void ApplyMeasurement_FirstAcceptAlwaysSnaps()
        {
            var state = RelocalizationFilter.InitialState();
            var measurement = MakeMapLocalization();
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
        public void ApplyMeasurement_PitchInputProducesYawOnlyAlignment()
        {
            // Two degrees of pitch in cameraFromMap. With the old 6 DOF + gravity-snap path, this
            // would push a map point at distance D vertically by ~D·sin(2°). The 4 DOF projection
            // must extract zero yaw and produce an alignment that cannot lift any ECEF point.
            var pitchRotation = quaternion.AxisAngle(new float3(1, 0, 0), math.radians(2f));
            var measurement = MakeMapLocalization(cameraFromMapRotation: pitchRotation);
            var frame = new CameraFrame
            {
                CameraTranslationUnityWorldFromCamera = float3.zero,
                CameraRotationUnityWorldFromCamera = quaternion.identity,
            };

            var result = RelocalizationFilter.ApplyMeasurement(RelocalizationFilter.InitialState(), measurement, frame);

            Assert.That(result.NewState.Yaw, Is.EqualTo(0.0).Within(1e-9));
            var alignment = RelocalizationFilter.BuildAlignment(result.NewState.Yaw, result.NewState.Translation);
            var ecefPointAt20m = new double3(0, 0, 20);
            var unityPoint = math.transform(alignment, ecefPointAt20m);
            Assert.That(unityPoint.y - result.NewState.Translation.y, Is.EqualTo(0.0).Within(1e-9));
        }

        [Test]
        public void ApplyMeasurement_RejectionInflatesStoredCovariance()
        {
            var origin = new CameraFrame
            {
                CameraTranslationUnityWorldFromCamera = float3.zero,
                CameraRotationUnityWorldFromCamera = quaternion.identity,
            };
            var accepted = RelocalizationFilter.ApplyMeasurement(
                RelocalizationFilter.InitialState(),
                MakeMapLocalization(),
                origin
            ).NewState;
            var sigmaAfterAccept = accepted.AlignmentCovariance;

            var jumped = new CameraFrame
            {
                CameraTranslationUnityWorldFromCamera = new float3(10f, 0f, 0f),
                CameraRotationUnityWorldFromCamera = quaternion.identity,
            };
            var rejected = RelocalizationFilter.ApplyMeasurement(accepted, MakeMapLocalization(), jumped);

            Assert.That(rejected.Rejection, Is.EqualTo(MeasurementRejection.InnovationGate));
            // Motion noise (0.01·10)² = 1e-2 dwarfs the 1e-4 per-tick base term.
            for (int i = 1; i < 4; i++)
                Assert.That(
                    rejected.NewState.AlignmentCovariance[i, i],
                    Is.GreaterThan(sigmaAfterAccept[i, i] + 9e-3),
                    $"diag[{i}] did not absorb motion-proportional process noise"
                );
        }

        [Test]
        public void ApplyMeasurement_RejectionRecoversAfterRepeatedJumpMeasurements()
        {
            var measurement = MakeMapLocalization();
            var state = RelocalizationFilter
                .ApplyMeasurement(
                    RelocalizationFilter.InitialState(),
                    measurement,
                    new CameraFrame
                    {
                        CameraTranslationUnityWorldFromCamera = float3.zero,
                        CameraRotationUnityWorldFromCamera = quaternion.identity,
                    }
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
        public void ApplyMeasurement_RepeatedRejectionsIncrementConsecutiveRejections()
        {
            var measurement = MakeMapLocalization();
            var state = RelocalizationFilter
                .ApplyMeasurement(
                    RelocalizationFilter.InitialState(),
                    measurement,
                    new CameraFrame
                    {
                        CameraTranslationUnityWorldFromCamera = float3.zero,
                        CameraRotationUnityWorldFromCamera = quaternion.identity,
                    }
                )
                .NewState;
            var jumpedFrame = new CameraFrame
            {
                CameraTranslationUnityWorldFromCamera = new float3(50f, 0f, 0f),
                CameraRotationUnityWorldFromCamera = quaternion.identity,
            };

            for (int i = 1; i <= 3; i++)
            {
                var step = RelocalizationFilter.ApplyMeasurement(state, measurement, jumpedFrame);
                Assert.That(step.Rejection, Is.EqualTo(MeasurementRejection.InnovationGate), $"iteration {i} not rejected");
                Assert.That(step.NewState.ConsecutiveRejections, Is.EqualTo(i));
                state = step.NewState;
            }
        }

        [Test]
        public void ApplyMeasurement_RejectionCapsCovarianceAtBootstrap()
        {
            var bootstrap = RelocalizationFilter.BootstrapCovariance();
            var oversized = bootstrap.Clone();
            for (int i = 0; i < 4; i++)
                oversized[i, i] = bootstrap[i, i] * 10.0;
            var state = RelocalizationFilter.InitialState();
            state.HasAcceptedMeasurement = true;
            state.LastAcceptedVioPosition = new double3(0, 0, 0);
            state.AlignmentCovariance = oversized;
            var jumped = new CameraFrame
            {
                CameraTranslationUnityWorldFromCamera = new float3(2000f, 0f, 0f),
                CameraRotationUnityWorldFromCamera = quaternion.identity,
            };

            var result = RelocalizationFilter.ApplyMeasurement(state, MakeMapLocalization(), jumped);

            Assert.That(result.Rejection, Is.EqualTo(MeasurementRejection.InnovationGate));
            for (int i = 0; i < 4; i++)
                Assert.That(
                    result.NewState.AlignmentCovariance[i, i],
                    Is.LessThanOrEqualTo(bootstrap[i, i] + 1e-9),
                    $"diag[{i}] exceeded bootstrap cap"
                );
        }

        [Test]
        public void ShiftMagnitudeSquared_SamePose_IsZero()
        {
            var sigma = Matrix<double>.Build.DenseIdentity(4);

            var shift = RelocalizationFilter.ShiftMagnitudeSquared(0.5, new double3(1, 2, 3), 0.5, new double3(1, 2, 3), sigma);

            Assert.That(shift, Is.EqualTo(0.0).Within(1e-9));
        }

        [Test]
        public void WrapAngle_WrapsToHalfOpenIntervalAroundPi()
        {
            Assert.That(MathUtil.WrapAngle(0.0), Is.EqualTo(0.0));
            Assert.That(MathUtil.WrapAngle(math.PI_DBL), Is.EqualTo(math.PI_DBL).Within(1e-9));
            Assert.That(MathUtil.WrapAngle(-math.PI_DBL), Is.EqualTo(math.PI_DBL).Within(1e-9));
            Assert.That(MathUtil.WrapAngle(3.0 * math.PI_DBL), Is.EqualTo(math.PI_DBL).Within(1e-9));
            Assert.That(MathUtil.WrapAngle(math.PI_DBL + 0.5), Is.EqualTo(-math.PI_DBL + 0.5).Within(1e-9));
            Assert.That(MathUtil.WrapAngle(-math.PI_DBL - 0.5), Is.EqualTo(math.PI_DBL - 0.5).Within(1e-9));
        }

        [Test]
        public void YawFromRotation_PureYawIsExtractedExactly()
        {
            var yaw = math.radians(37.0);
            var rotation = MathUtil.YawOnlyRotation(yaw);

            Assert.That(MathUtil.YawFromRotation(rotation), Is.EqualTo(yaw).Within(1e-6));
        }

        [Test]
        public void YawFromRotation_PurePitchExtractsZeroYaw()
        {
            var rotation = quaternion.AxisAngle(new float3(1, 0, 0), math.radians(15f)).ToDouble3x3();

            Assert.That(MathUtil.YawFromRotation(rotation), Is.EqualTo(0.0).Within(1e-6));
        }

        private static MapLocalization MakeMapLocalization(
            double tightConfidence = 0.99,
            double looseConfidence = 0.99,
            quaternion? cameraFromMapRotation = null
        )
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
            var rotation = cameraFromMapRotation ?? quaternion.identity;
            var cameraFromMap = new PlaceframeApiClient.Model.Transform(
                translation: new Float3(0, 0, 0),
                rotation: new Float4(rotation.value.x, rotation.value.y, rotation.value.z, rotation.value.w)
            );
            var identityTransform = new PlaceframeApiClient.Model.Transform(
                translation: new Float3(0, 0, 0),
                rotation: new Float4(0, 0, 0, 1)
            );
            return new MapLocalization(
                id: System.Guid.NewGuid(),
                cameraFromMapTransform: cameraFromMap,
                mapTransform: identityTransform,
                metrics: metrics
            );
        }
    }
}
