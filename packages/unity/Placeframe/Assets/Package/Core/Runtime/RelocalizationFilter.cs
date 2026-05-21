using System.Collections.Generic;
using MathNet.Numerics.LinearAlgebra;
using PlaceframeApiClient.Model;
using Unity.Mathematics;

namespace Placeframe.Core
{
    public struct AlignmentUncertainty
    {
        public float TranslationStdMeters;
        public float RotationStdDegrees;
    }

    // The alignment is parameterised as 4 DOF: yaw around Unity +Y plus an R³ translation.
    // Pitch and roll are constrained to zero — gravity alignment of the map is delegated to the
    // reconstructor's anchor selection rather than absorbed per-measurement by the filter.
    // Covariance ordering: [yaw, tx, ty, tz].
    public struct FilterState
    {
        public double Yaw;
        public double3 Translation;
        public Matrix<double> AlignmentCovariance;
        public double YawCurrent;
        public double3 TranslationCurrent;
        public double YawSlewStart;
        public double3 TranslationSlewStart;
        public float SlewProgress;
        public double3? LastAcceptedVioPosition;
        public bool HasAcceptedMeasurement;
        public int ConsecutiveRejections;
        public LocalizationMetrics MostRecentMetrics;
    }

    public enum MeasurementRejection
    {
        None,
        InnovationGate,
    }

    public struct StepResult
    {
        public FilterState NewState;
        public bool TransformChanged;
        public MeasurementRejection Rejection;
        public double InnovationMahalanobisSquared;
        public Vector<double> InnovationResidual;
        public Matrix<double> SigmaPredicted;
        public bool HadAcceptedMeasurementBeforeStep;
    }

    public static class RelocalizationFilter
    {
        // Chi-square 99% critical value for 4 degrees of freedom — outlier gate threshold.
        public const double Chi2_99_4dof = 13.28;

        // Snap (don't slew) when the Bayesian update shifts the alignment more than this many σ.
        public const double SnapThresholdSigmasSquared = 36.0;

        public const float SlewDurationSeconds = 0.5f;

        // Per meter of VIO motion, σ grows by 1 cm on translation and 0.01 rad ≈ 0.57° on yaw.
        public const double DriftPerMeter = 0.01;

        // Base process noise added per measurement regardless of VIO motion, so σ_posterior
        // cannot shrink unboundedly during stationary observation. Without this, repeated stationary
        // measurements drive σ_posterior below σ_meas/√N and the innovation gate locks the filter
        // onto its first cluster, rejecting all further measurements.
        public const double BaseProcessNoiseTranslationVariancePerTick = 1e-4;
        public const double BaseProcessNoiseYawVariancePerTick = 1e-6;

        public const double BootstrapSigmaTranslationMeters = 100.0;
        public static readonly double BootstrapSigmaYawRadians = math.PI_DBL;

        // Indices of (ωy, νx, νy, νz) inside the 6 DOF (ωx, ωy, ωz, νx, νy, νz) pycolmap covariance.
        // Diagonal-dominant projection: yaw ← ωy, translation ← ν.
        private static readonly int[] FourDofIndicesIn6Dof = { 1, 3, 4, 5 };

        public struct Innovation
        {
            public Vector<double> Residual;
            public Matrix<double> Covariance;
            public double MahalanobisSquared;
        }

        public struct PosteriorUpdate
        {
            public double NewYaw;
            public double3 NewTranslation;
            public Matrix<double> NewCovariance;
        }

        public static FilterState InitialState() =>
            new FilterState
            {
                Yaw = 0.0,
                Translation = double3.zero,
                AlignmentCovariance = BootstrapCovariance(),
                YawCurrent = 0.0,
                TranslationCurrent = double3.zero,
                YawSlewStart = 0.0,
                TranslationSlewStart = double3.zero,
                SlewProgress = 1f,
                LastAcceptedVioPosition = null,
                HasAcceptedMeasurement = false,
                ConsecutiveRejections = 0,
                MostRecentMetrics = null,
            };

        public static StepResult ApplyMeasurement(
            FilterState state,
            MapLocalization localizationResult,
            CameraFrame frame
        )
        {
            var metrics = localizationResult.Metrics;
            var measurement = ComputeAlignmentFromResult(localizationResult, frame);
            var sigmaMeas = ProjectCovariance(BuildCovarianceMatrix(metrics.MeasurementCovariance));
            var currentVioPosition = (double3)(float3)frame.CameraTranslationUnityWorldFromCamera;
            var sigmaPredicted =
                state.AlignmentCovariance + ProcessNoise(currentVioPosition, state.LastAcceptedVioPosition);
            var innovation = ComputeInnovation(
                state.Yaw,
                state.Translation,
                sigmaPredicted,
                measurement.Yaw,
                measurement.Translation,
                sigmaMeas
            );

            if (innovation.MahalanobisSquared > Chi2_99_4dof)
            {
                var bootstrap = BootstrapCovariance();
                for (var i = 0; i < 4; i++)
                    sigmaPredicted[i, i] = math.min(sigmaPredicted[i, i], bootstrap[i, i]);

                var rejectedState = state;
                rejectedState.AlignmentCovariance = sigmaPredicted;
                rejectedState.ConsecutiveRejections = state.ConsecutiveRejections + 1;

                return new StepResult
                {
                    NewState = rejectedState,
                    Rejection = MeasurementRejection.InnovationGate,
                    InnovationMahalanobisSquared = innovation.MahalanobisSquared,
                    InnovationResidual = innovation.Residual,
                    SigmaPredicted = sigmaPredicted,
                    HadAcceptedMeasurementBeforeStep = state.HasAcceptedMeasurement,
                };
            }

            var posterior = KalmanUpdate(
                state.Yaw,
                state.Translation,
                sigmaPredicted,
                innovation.Residual,
                innovation.Covariance
            );

            var newState = state;
            newState.Yaw = posterior.NewYaw;
            newState.Translation = posterior.NewTranslation;
            newState.AlignmentCovariance = posterior.NewCovariance;

            var shouldSnap = !state.HasAcceptedMeasurement;
            if (!shouldSnap)
            {
                var shiftMagSquared = ShiftMagnitudeSquared(
                    state.YawCurrent,
                    state.TranslationCurrent,
                    posterior.NewYaw,
                    posterior.NewTranslation,
                    posterior.NewCovariance
                );
                shouldSnap = shiftMagSquared > SnapThresholdSigmasSquared;
            }

            var transformChanged = false;
            if (shouldSnap)
            {
                newState.YawSlewStart = posterior.NewYaw;
                newState.TranslationSlewStart = posterior.NewTranslation;
                newState.YawCurrent = posterior.NewYaw;
                newState.TranslationCurrent = posterior.NewTranslation;
                newState.SlewProgress = 1f;
                transformChanged = true;
            }
            else
            {
                newState.YawSlewStart = state.YawCurrent;
                newState.TranslationSlewStart = state.TranslationCurrent;
                newState.SlewProgress = 0f;
            }

            newState.HasAcceptedMeasurement = true;
            newState.LastAcceptedVioPosition = currentVioPosition;
            newState.ConsecutiveRejections = 0;
            newState.MostRecentMetrics = metrics;

            return new StepResult { NewState = newState, TransformChanged = transformChanged };
        }

        public static StepResult TickSlew(FilterState state, float deltaSeconds)
        {
            if (state.SlewProgress >= 1f)
                return new StepResult { NewState = state };

            var newState = state;
            newState.SlewProgress = math.min(1f, state.SlewProgress + deltaSeconds / SlewDurationSeconds);
            var t = SmoothStep(newState.SlewProgress);
            var yawDelta = MathUtil.WrapAngle(state.Yaw - state.YawSlewStart);
            newState.YawCurrent = MathUtil.WrapAngle(state.YawSlewStart + yawDelta * t);
            newState.TranslationCurrent = math.lerp(state.TranslationSlewStart, state.Translation, t);
            if (newState.SlewProgress >= 1f)
            {
                newState.YawCurrent = state.Yaw;
                newState.TranslationCurrent = state.Translation;
            }

            return new StepResult { NewState = newState, TransformChanged = true };
        }

        public static StepResult Reset(FilterState state, double newYaw, double3 newTranslation)
        {
            var wrappedYaw = MathUtil.WrapAngle(newYaw);
            var newState = new FilterState
            {
                Yaw = wrappedYaw,
                Translation = newTranslation,
                AlignmentCovariance = BootstrapCovariance(),
                YawCurrent = wrappedYaw,
                TranslationCurrent = newTranslation,
                YawSlewStart = wrappedYaw,
                TranslationSlewStart = newTranslation,
                SlewProgress = 1f,
                LastAcceptedVioPosition = null,
                HasAcceptedMeasurement = false,
                ConsecutiveRejections = 0,
                MostRecentMetrics = state.MostRecentMetrics,
            };

            return new StepResult { NewState = newState, TransformChanged = true };
        }

        public static StepResult Reset(FilterState state, double4x4 newAlignment)
        {
            var rotation = newAlignment.RotationMatrix();
            var yaw = MathUtil.YawFromRotation(rotation);
            return Reset(state, yaw, newAlignment.Position());
        }

        public static Matrix<double> BootstrapCovariance()
        {
            var yawVar = BootstrapSigmaYawRadians * BootstrapSigmaYawRadians;
            var transVar = BootstrapSigmaTranslationMeters * BootstrapSigmaTranslationMeters;
            return Matrix<double>.Build.DenseOfDiagonalArray(new[] { yawVar, transVar, transVar, transVar });
        }

        public static Matrix<double> BuildCovarianceMatrix(List<List<double>> covariance) =>
            Matrix<double>.Build.Dense(6, 6, (r, c) => covariance[r][c]);

        // Projects a 6 DOF pycolmap covariance (ωx, ωy, ωz, νx, νy, νz) down to the 4 DOF
        // [yaw, tx, ty, tz] state. Diagonal-dominant approximation: discards cross-correlation
        // between the dropped pitch/roll dimensions and the kept dimensions. Full Jacobian would
        // add cross-terms scaling with |t_mapFromCamera|; revisit if the filter under-reports
        // confidence at large distances from the map origin.
        public static Matrix<double> ProjectCovariance(Matrix<double> sigma6)
        {
            var sigma4 = Matrix<double>.Build.Dense(4, 4);
            for (var i = 0; i < 4; i++)
                for (var j = 0; j < 4; j++)
                    sigma4[i, j] = sigma6[FourDofIndicesIn6Dof[i], FourDofIndicesIn6Dof[j]];
            return sigma4;
        }

        public static Matrix<double> ProcessNoise(double3 currentVioPosition, double3? lastAcceptedVioPosition)
        {
            var noise = Matrix<double>.Build.DenseOfDiagonalArray(
                new[]
                {
                    BaseProcessNoiseYawVariancePerTick,
                    BaseProcessNoiseTranslationVariancePerTick,
                    BaseProcessNoiseTranslationVariancePerTick,
                    BaseProcessNoiseTranslationVariancePerTick,
                }
            );

            if (lastAcceptedVioPosition == null)
                return noise;

            // VIO drift is modeled as proportional to translated distance and applied uniformly
            // to all four dimensions: σ_translation in meters, σ_yaw in radians. Rotation-only
            // motion contributes zero noise here — a known simplification, since yaw drift without
            // translation is small and hard to attribute without an IMU bias model.
            var deltaTranslation = math.length(currentVioPosition - lastAcceptedVioPosition.Value);
            var sigma = DriftPerMeter * deltaTranslation;
            var motionVariance = sigma * sigma;
            return noise + Matrix<double>.Build.DenseDiagonal(4, 4, motionVariance);
        }

        public static double MahalanobisSquared(Vector<double> residual, Matrix<double> covariance)
        {
            var inv = covariance.Inverse();
            var product = inv * residual;
            return residual.DotProduct(product);
        }

        public static float SmoothStep(float t) => t * t * (3f - 2f * t);

        public static AlignmentUncertainty SummariseCovariance(Matrix<double> sigma)
        {
            var translationVarianceSum = sigma[1, 1] + sigma[2, 2] + sigma[3, 3];
            return new AlignmentUncertainty
            {
                TranslationStdMeters = (float)math.sqrt(translationVarianceSum),
                RotationStdDegrees = (float)(math.sqrt(sigma[0, 0]) * (180.0 / math.PI_DBL)),
            };
        }

        public struct Measurement
        {
            public double Yaw;
            public double3 Translation;
        }

        public static Measurement ComputeAlignmentFromResult(MapLocalization localizationResult, CameraFrame frame)
        {
            var translationCameraFromMap = localizationResult.CameraFromMapTransform.Translation.ToDouble3();
            var rotationCameraFromMap = localizationResult
                .CameraFromMapTransform.Rotation.ToMathematicsQuaternion()
                .ToDouble3x3();

            var translationEcefFromMap = localizationResult.MapTransform.Translation.ToDouble3();
            var rotationEcefFromMap = localizationResult.MapTransform.Rotation.ToMathematicsQuaternion().ToDouble3x3();

            (translationEcefFromMap, rotationEcefFromMap) = LocationUtilities.ChangeBasisUnityFromEcef(
                translationEcefFromMap,
                rotationEcefFromMap
            );

            var translationUnityWorldFromCamera = (double3)(float3)frame.CameraTranslationUnityWorldFromCamera;
            var rotationUnityWorldFromCamera = ((quaternion)frame.CameraRotationUnityWorldFromCamera).ToDouble3x3();

            // Camera position in ECEF (Unity basis), via the map.
            var rotationMapFromCamera = math.transpose(rotationCameraFromMap);
            var translationMapFromCamera = math.mul(-rotationMapFromCamera, translationCameraFromMap);
            var translationEcefFromCamera =
                math.mul(rotationEcefFromMap, translationMapFromCamera) + translationEcefFromMap;

            // Composed raw rotation Unity ← ECEF, before the yaw-only projection.
            var rotationUnityFromMap = math.mul(rotationUnityWorldFromCamera, rotationCameraFromMap);
            var rotationUnityFromEcef = math.mul(rotationUnityFromMap, rotationEcefFromMap);

            var yawMeas = MathUtil.YawFromRotation(rotationUnityFromEcef);
            var rotationYawOnly = MathUtil.YawOnlyRotation(yawMeas);

            // Translation: anchored on the camera. Map origin's vertical offset is whatever the
            // map says; the yaw-only rotation never lifts it spuriously.
            var translationMeas =
                translationUnityWorldFromCamera - math.mul(rotationYawOnly, translationEcefFromCamera);

            return new Measurement { Yaw = yawMeas, Translation = translationMeas };
        }

        public static Innovation ComputeInnovation(
            double yawState,
            double3 translationState,
            Matrix<double> sigmaPredicted,
            double yawMeas,
            double3 translationMeas,
            Matrix<double> sigmaMeas
        )
        {
            var deltaYaw = MathUtil.WrapAngle(yawMeas - yawState);
            var deltaTranslation = translationMeas - translationState;
            var residual = Vector<double>.Build.DenseOfArray(
                new[] { deltaYaw, deltaTranslation.x, deltaTranslation.y, deltaTranslation.z }
            );
            var innovationCov = sigmaPredicted + sigmaMeas;
            return new Innovation
            {
                Residual = residual,
                Covariance = innovationCov,
                MahalanobisSquared = MahalanobisSquared(residual, innovationCov),
            };
        }

        public static PosteriorUpdate KalmanUpdate(
            double yawState,
            double3 translationState,
            Matrix<double> sigmaPredicted,
            Vector<double> residual,
            Matrix<double> innovationCovariance
        )
        {
            var kalmanGain = sigmaPredicted * innovationCovariance.Inverse();
            var update = kalmanGain * residual;
            var newYaw = MathUtil.WrapAngle(yawState + update[0]);
            var newTranslation = translationState + new double3(update[1], update[2], update[3]);
            var newCov = (Matrix<double>.Build.DenseIdentity(4) - kalmanGain) * sigmaPredicted;
            return new PosteriorUpdate
            {
                NewYaw = newYaw,
                NewTranslation = newTranslation,
                NewCovariance = newCov,
            };
        }

        public static double ShiftMagnitudeSquared(
            double yawFrom,
            double3 translationFrom,
            double yawTo,
            double3 translationTo,
            Matrix<double> covariance
        )
        {
            var deltaYaw = MathUtil.WrapAngle(yawTo - yawFrom);
            var deltaTranslation = translationTo - translationFrom;
            var residual = Vector<double>.Build.DenseOfArray(
                new[] { deltaYaw, deltaTranslation.x, deltaTranslation.y, deltaTranslation.z }
            );
            return MahalanobisSquared(residual, covariance);
        }

        public static double4x4 BuildAlignment(double yaw, double3 translation) =>
            Double4x4.FromTranslationRotation(translation, MathUtil.YawOnlyRotation(yaw));
    }
}
