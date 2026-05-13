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

    public struct FilterState
    {
        public double4x4 AlignmentMean;
        public Matrix<double> AlignmentCovariance;
        public double4x4 AlignmentCurrent;
        public double4x4 AlignmentCurrentInverse;
        public double4x4 SlewStart;
        public float SlewProgress;
        public double3? LastAcceptedVioPosition;
        public bool HasAcceptedMeasurement;
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
        // Chi-square 99% critical value for 6 degrees of freedom — outlier gate threshold.
        public const double Chi2_99_6dof = 16.81;

        // Snap (don't slew) when the Bayesian update shifts the alignment more than this many σ.
        public const double SnapThresholdSigmasSquared = 36.0;

        public const float SlewDurationSeconds = 0.5f;

        // Per meter of VIO motion, σ_translation grows by 1cm and σ_rotation by 0.01 rad ≈ 0.57°.
        public const double DriftPerMeter = 0.01;

        // Base process noise added per measurement regardless of VIO motion, so σ_posterior
        // cannot shrink unboundedly during stationary observation. Without this, ~30 stationary
        // measurements drive σ_posterior below σ_meas/√N and the innovation gate locks the filter
        // onto its first cluster, rejecting all further measurements. Sized to keep steady-state
        // σ_posterior at roughly σ_meas/3 given a 1Hz query cadence and the current bootstrapped
        // σ_meas (translation ≈ 10cm, rotation tight from PnP Hessian). Re-tuned in Phase 3 once
        // σ_meas is fit from real data.
        public const double BaseProcessNoiseTranslationVariancePerTick = 1e-4;
        public const double BaseProcessNoiseRotationVariancePerTick = 1e-6;

        public const double BootstrapSigmaTranslationMeters = 100.0;
        public static readonly double BootstrapSigmaRotationRadians = math.PI_DBL;

        public struct Innovation
        {
            public Vector<double> Residual;
            public Matrix<double> Covariance;
            public double MahalanobisSquared;
        }

        public struct PosteriorUpdate
        {
            public double4x4 NewMean;
            public Matrix<double> NewCovariance;
        }

        public static FilterState InitialState() =>
            new FilterState
            {
                AlignmentMean = double4x4.identity,
                AlignmentCovariance = BootstrapCovariance(),
                AlignmentCurrent = double4x4.identity,
                AlignmentCurrentInverse = double4x4.identity,
                SlewStart = double4x4.identity,
                SlewProgress = 1f,
                LastAcceptedVioPosition = null,
                HasAcceptedMeasurement = false,
                MostRecentMetrics = null,
            };

        // Bayesian update on the SE(3) alignment posterior. VIO motion only inflates Σ (not the mean).
        // Returns NewState plus a flag indicating whether the visible transform changed (snap).
        public static StepResult ApplyMeasurement(
            FilterState state,
            MapLocalization localizationResult,
            CameraFrame frame
        )
        {
            var metrics = localizationResult.Metrics;
            var measurementMean = ComputeAlignmentFromResult(localizationResult, frame);
            var sigmaMeas = BuildCovarianceMatrix(metrics.MeasurementCovariance);
            var currentVioPosition = (double3)(float3)frame.CameraTranslationUnityWorldFromCamera;
            var sigmaPredicted =
                state.AlignmentCovariance + ProcessNoise(currentVioPosition, state.LastAcceptedVioPosition);
            var innovation = ComputeInnovation(state.AlignmentMean, sigmaPredicted, measurementMean, sigmaMeas);

            if (innovation.MahalanobisSquared > Chi2_99_6dof)
                return new StepResult
                {
                    NewState = state,
                    Rejection = MeasurementRejection.InnovationGate,
                    InnovationMahalanobisSquared = innovation.MahalanobisSquared,
                    InnovationResidual = innovation.Residual,
                    SigmaPredicted = sigmaPredicted,
                    HadAcceptedMeasurementBeforeStep = state.HasAcceptedMeasurement,
                };

            var posterior = KalmanUpdate(
                state.AlignmentMean,
                sigmaPredicted,
                innovation.Residual,
                innovation.Covariance
            );

            var newState = state;
            newState.AlignmentMean = posterior.NewMean;
            newState.AlignmentCovariance = posterior.NewCovariance;

            // First accept always snaps — bootstrap covariance is intentionally large and the snap-vs-slew
            // shift_mag would be ill-conditioned against a near-singular Σ_new on the first update.
            var shouldSnap = !state.HasAcceptedMeasurement;
            if (!shouldSnap)
            {
                var shiftMagSquared = ShiftMagnitudeSquared(
                    state.AlignmentCurrent,
                    posterior.NewMean,
                    posterior.NewCovariance
                );
                shouldSnap = shiftMagSquared > SnapThresholdSigmasSquared;
            }

            var transformChanged = false;
            if (shouldSnap)
            {
                newState.SlewStart = posterior.NewMean;
                newState.AlignmentCurrent = posterior.NewMean;
                newState.AlignmentCurrentInverse = math.inverse(posterior.NewMean);
                newState.SlewProgress = 1f;
                transformChanged = true;
            }
            else
            {
                newState.SlewStart = state.AlignmentCurrent;
                newState.SlewProgress = 0f;
            }

            newState.HasAcceptedMeasurement = true;
            newState.LastAcceptedVioPosition = currentVioPosition;
            newState.MostRecentMetrics = metrics;

            return new StepResult { NewState = newState, TransformChanged = transformChanged };
        }

        // Advances the slew toward AlignmentMean by deltaSeconds. No-op when slew is settled.
        public static StepResult TickSlew(FilterState state, float deltaSeconds)
        {
            if (state.SlewProgress >= 1f)
                return new StepResult { NewState = state };

            var newState = state;
            newState.SlewProgress = math.min(1f, state.SlewProgress + deltaSeconds / SlewDurationSeconds);
            var t = SmoothStep(newState.SlewProgress);
            newState.AlignmentCurrent = Double4x4.Interpolate(state.SlewStart, state.AlignmentMean, t);
            if (newState.SlewProgress >= 1f)
                newState.AlignmentCurrent = state.AlignmentMean;
            newState.AlignmentCurrentInverse = math.inverse(newState.AlignmentCurrent);

            return new StepResult { NewState = newState, TransformChanged = true };
        }

        // Externally-driven reset to a known alignment. Clears filter history and re-bootstraps Σ.
        public static StepResult Reset(FilterState state, double4x4 newAlignment)
        {
            var newState = new FilterState
            {
                AlignmentMean = newAlignment,
                AlignmentCovariance = BootstrapCovariance(),
                AlignmentCurrent = newAlignment,
                AlignmentCurrentInverse = math.inverse(newAlignment),
                SlewStart = newAlignment,
                SlewProgress = 1f,
                LastAcceptedVioPosition = null,
                HasAcceptedMeasurement = false,
                MostRecentMetrics = state.MostRecentMetrics,
            };

            return new StepResult { NewState = newState, TransformChanged = true };
        }

        public static Matrix<double> BootstrapCovariance()
        {
            var rotVar = BootstrapSigmaRotationRadians * BootstrapSigmaRotationRadians;
            var transVar = BootstrapSigmaTranslationMeters * BootstrapSigmaTranslationMeters;
            return Matrix<double>.Build.DenseOfDiagonalArray(
                new[] { rotVar, rotVar, rotVar, transVar, transVar, transVar }
            );
        }

        public static Matrix<double> BuildCovarianceMatrix(List<List<double>> covariance) =>
            Matrix<double>.Build.Dense(6, 6, (r, c) => covariance[r][c]);

        public static Matrix<double> ProcessNoise(double3 currentVioPosition, double3? lastAcceptedVioPosition)
        {
            var noise = Matrix<double>.Build.DenseOfDiagonalArray(
                new[]
                {
                    BaseProcessNoiseRotationVariancePerTick,
                    BaseProcessNoiseRotationVariancePerTick,
                    BaseProcessNoiseRotationVariancePerTick,
                    BaseProcessNoiseTranslationVariancePerTick,
                    BaseProcessNoiseTranslationVariancePerTick,
                    BaseProcessNoiseTranslationVariancePerTick,
                }
            );

            if (lastAcceptedVioPosition == null)
                return noise;

            // VIO drift is modeled as proportional to translated distance and applied uniformly to all 6
            // tangent dimensions: σ_translation in meters, σ_rotation in radians. Rotation-only motion
            // contributes zero noise here — a known simplification; rotational VIO drift is a smaller
            // effect than translational and harder to attribute without an IMU bias model.
            var deltaTranslation = math.length(currentVioPosition - lastAcceptedVioPosition.Value);
            var sigma = DriftPerMeter * deltaTranslation;
            var motionVariance = sigma * sigma;
            return noise + Matrix<double>.Build.DenseDiagonal(6, 6, motionVariance);
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
            var rotationVarianceSum = sigma[0, 0] + sigma[1, 1] + sigma[2, 2];
            var translationVarianceSum = sigma[3, 3] + sigma[4, 4] + sigma[5, 5];
            return new AlignmentUncertainty
            {
                TranslationStdMeters = (float)math.sqrt(translationVarianceSum),
                RotationStdDegrees = (float)(math.sqrt(rotationVarianceSum) * (180.0 / math.PI_DBL)),
            };
        }

        public static double4x4 ComputeAlignmentFromResult(MapLocalization localizationResult, CameraFrame frame)
        {
            // Get the transform from the map to the camera (The inverse of the camera's pose in the map)
            var translationCameraFromMap = localizationResult.CameraFromMapTransform.Translation.ToDouble3();
            var rotationCameraFromMap = localizationResult
                .CameraFromMapTransform.Rotation.ToMathematicsQuaternion()
                .ToDouble3x3();

            // Get the transform from the map to the ECEF reference frame (the map's ECEF pose)
            var translationEcefFromMap = localizationResult.MapTransform.Translation.ToDouble3();
            var rotationEcefFromMap = localizationResult.MapTransform.Rotation.ToMathematicsQuaternion().ToDouble3x3();

            // Change the basis of the map's pose to Unity's conventions
            (translationEcefFromMap, rotationEcefFromMap) = LocationUtilities.ChangeBasisUnityFromEcef(
                translationEcefFromMap,
                rotationEcefFromMap
            );

            // Get the transform from the camera to Unity world (the camera's pose in the Unity world)
            var translationUnityWorldFromCamera = (float3)frame.CameraTranslationUnityWorldFromCamera;
            // TODO: Adjust unity rotation to account for phone orientation (portrait vs landscape).
            var rotationUnityWorldFromCamera = math.mul(
                ((quaternion)frame.CameraRotationUnityWorldFromCamera).ToDouble3x3(),
                quaternion.AxisAngle(new float3(0f, 0f, 1f), math.radians(0f)).ToDouble3x3()
            );

            // Compute the transform from the map to Unity world
            var rotationUnityFromMap = math.mul(rotationUnityWorldFromCamera, rotationCameraFromMap);

            // Align matrix up with unity world up
            var right = math.rotate(rotationUnityFromMap.ToQuaternion(), new float3(1, 0, 0));
            var forward = math.cross(right, new float3(0, 1, 0));
            rotationUnityFromMap = quaternion.LookRotation(forward, new float3(0, 1, 0)).ToDouble3x3();

            var translationUnityFromMap =
                math.mul(rotationUnityWorldFromCamera, translationCameraFromMap) + translationUnityWorldFromCamera;

            var transformUnityFromMap = Double4x4.FromTranslationRotation(
                translationUnityFromMap,
                rotationUnityFromMap
            );

            return math.mul(
                transformUnityFromMap,
                math.inverse(Double4x4.FromTranslationRotation(translationEcefFromMap, rotationEcefFromMap))
            );
        }

        public static Innovation ComputeInnovation(
            double4x4 currentMean,
            Matrix<double> sigmaPredicted,
            double4x4 measurementMean,
            Matrix<double> sigmaMeas
        )
        {
            var residual = Se3.Log(math.mul(math.inverse(currentMean), measurementMean));
            var innovationCov = sigmaPredicted + sigmaMeas;
            return new Innovation
            {
                Residual = residual,
                Covariance = innovationCov,
                MahalanobisSquared = MahalanobisSquared(residual, innovationCov),
            };
        }

        public static PosteriorUpdate KalmanUpdate(
            double4x4 currentMean,
            Matrix<double> sigmaPredicted,
            Vector<double> residual,
            Matrix<double> innovationCovariance
        )
        {
            var kalmanGain = sigmaPredicted * innovationCovariance.Inverse();
            var residualUpdate = kalmanGain * residual;
            var newMean = math.mul(currentMean, Se3.Exp(residualUpdate));
            var newCov = (Matrix<double>.Build.DenseIdentity(6) - kalmanGain) * sigmaPredicted;
            return new PosteriorUpdate { NewMean = newMean, NewCovariance = newCov };
        }

        public static double ShiftMagnitudeSquared(double4x4 from, double4x4 to, Matrix<double> covariance)
        {
            var residual = Se3.Log(math.mul(math.inverse(from), to));
            return MahalanobisSquared(residual, covariance);
        }
    }
}
