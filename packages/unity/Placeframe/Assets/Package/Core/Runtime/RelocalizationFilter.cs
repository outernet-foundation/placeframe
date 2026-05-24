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
        public int ConsecutiveRejections;
        public LocalizationMetrics MostRecentMetrics;
    }

    public enum MeasurementRejection
    {
        None,
        InnovationGate,
    }

    public struct ApplyMeasurementOptions
    {
        public bool BypassInnovationGate;
        public bool BypassKalman;
    }

    public struct Measurement
    {
        public double3x3 RotationUnityFromEcef;
        public double3 Translation;
        public double TiltRadians;
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
        public Measurement Measurement;
        public bool Snapped;
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
        // cannot shrink unboundedly during stationary observation. Without this, repeated stationary
        // measurements drive σ_posterior below σ_meas/√N and the innovation gate locks the filter
        // onto its first cluster, rejecting all further measurements.
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
                ConsecutiveRejections = 0,
                MostRecentMetrics = null,
            };

        public static StepResult ApplyMeasurement(
            FilterState state,
            MapLocalization localizationResult,
            CameraFrame frame,
            ApplyMeasurementOptions options = default
        )
        {
            var metrics = localizationResult.Metrics;
            var measurement = ComputeAlignmentFromResult(localizationResult, frame);
            var measurementMean = Double4x4.FromTranslationRotation(measurement.Translation, measurement.RotationUnityFromEcef);
            var sigmaMeas = BuildCovarianceMatrix(metrics.MeasurementCovariance);
            var currentVioPosition = (double3)(float3)frame.CameraTranslationUnityWorldFromCamera;
            var sigmaPredicted = state.AlignmentCovariance + ProcessNoise(currentVioPosition, state.LastAcceptedVioPosition);
            var innovation = ComputeInnovation(state.AlignmentMean, sigmaPredicted, measurementMean, sigmaMeas);

            if (!options.BypassInnovationGate && innovation.MahalanobisSquared > Chi2_99_6dof)
            {
                // Write sigmaPredicted back so process noise accumulates across rejections;
                // without the writeback the gate would stay closed at the same threshold
                // indefinitely. Per-diagonal cap at bootstrap prevents unbounded growth
                // that would eventually admit outliers as eagerly as good measurements.
                //
                // Motion-proportional inflation (0.01·|Δvio|)² alone only unlocks residuals
                // up to ~0.4-0.5 m on human-walk timescales: a 1 m residual requires ~22 m
                // of additional walking to clear the gate, and multi-meter residuals are
                // effectively unrecoverable from this path without a separate burst-rejection
                // escalation keyed on ConsecutiveRejections.
                var bootstrap = BootstrapCovariance();
                for (var i = 0; i < 6; i++)
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
                    Measurement = measurement,
                };
            }

            PosteriorUpdate posterior;
            if (options.BypassKalman)
            {
                posterior = new PosteriorUpdate { NewMean = measurementMean, NewCovariance = BootstrapCovariance() };
            }
            else
            {
                posterior = KalmanUpdate(state.AlignmentMean, sigmaPredicted, innovation.Residual, innovation.Covariance);
            }

            var newState = state;
            newState.AlignmentMean = posterior.NewMean;
            newState.AlignmentCovariance = posterior.NewCovariance;

            // First-accept-after-Reset commits the PnP result unconditionally as the filter mean.
            // If the localizer's first results are a wrong-but-coherent cluster (perceptual aliasing,
            // self-similar map regions, partial visibility), the Kalman posterior collapses around
            // that pose within a few accepts; subsequent correct measurements then arrive at
            // multi-meter residuals the innovation gate cannot reopen on human-walk timescales.
            // A multi-frame agreement check (K within-σ measurements before committing the first
            // mean) would gate this without changing steady-state behavior.
            var shouldSnap = !state.HasAcceptedMeasurement || options.BypassKalman;
            if (!shouldSnap)
            {
                var shiftMagSquared = ShiftMagnitudeSquared(state.AlignmentCurrent, posterior.NewMean, posterior.NewCovariance);
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
            newState.ConsecutiveRejections = 0;
            newState.MostRecentMetrics = metrics;

            return new StepResult
            {
                NewState = newState,
                TransformChanged = transformChanged,
                InnovationMahalanobisSquared = innovation.MahalanobisSquared,
                InnovationResidual = innovation.Residual,
                SigmaPredicted = sigmaPredicted,
                HadAcceptedMeasurementBeforeStep = state.HasAcceptedMeasurement,
                Measurement = measurement,
                Snapped = shouldSnap,
            };
        }

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
                ConsecutiveRejections = 0,
                MostRecentMetrics = state.MostRecentMetrics,
            };

            return new StepResult { NewState = newState, TransformChanged = true };
        }

        public static Matrix<double> BootstrapCovariance()
        {
            var rotVar = BootstrapSigmaRotationRadians * BootstrapSigmaRotationRadians;
            var transVar = BootstrapSigmaTranslationMeters * BootstrapSigmaTranslationMeters;
            return Matrix<double>.Build.DenseOfDiagonalArray(new[] { rotVar, rotVar, rotVar, transVar, transVar, transVar });
        }

        public static Matrix<double> BuildCovarianceMatrix(List<List<double>> covariance) => Matrix<double>.Build.Dense(6, 6, (r, c) => covariance[r][c]);

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

            // VIO drift is modeled as proportional to translated distance and applied uniformly
            // to all six tangent dimensions: σ_translation in meters, σ_rotation in radians.
            // Rotation-only motion contributes zero noise — a known simplification.
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

        public static Measurement ComputeAlignmentFromResult(MapLocalization localizationResult, CameraFrame frame)
        {
            var translationCameraFromMap = localizationResult.CameraFromMapTransform.Translation.ToDouble3();
            var rotationCameraFromMap = localizationResult.CameraFromMapTransform.Rotation.ToMathematicsQuaternion().ToDouble3x3();

            var translationEcefFromMap = localizationResult.MapTransform.Translation.ToDouble3();
            var rotationEcefFromMap = localizationResult.MapTransform.Rotation.ToMathematicsQuaternion().ToDouble3x3();

            (translationEcefFromMap, rotationEcefFromMap) = LocationUtilities.ChangeBasisUnityFromEcef(translationEcefFromMap, rotationEcefFromMap);

            var translationUnityWorldFromCamera = (double3)(float3)frame.CameraTranslationUnityWorldFromCamera;
            var rotationUnityWorldFromCamera = ((quaternion)frame.CameraRotationUnityWorldFromCamera).ToDouble3x3();

            // Camera position in ECEF (Unity basis), via the map.
            var rotationMapFromCamera = math.transpose(rotationCameraFromMap);
            var translationMapFromCamera = math.mul(-rotationMapFromCamera, translationCameraFromMap);
            var translationEcefFromCamera = math.mul(rotationEcefFromMap, translationMapFromCamera) + translationEcefFromMap;

            // Composed rotation Unity ← ECEF. MapTransform carries R_ecefFromMap, so composition
            // into R_unityFromEcef needs R_mapFromEcef = transpose(R_ecefFromMap).
            var rotationUnityFromMap = math.mul(rotationUnityWorldFromCamera, rotationCameraFromMap);
            var rotationUnityFromEcef = math.mul(rotationUnityFromMap, math.transpose(rotationEcefFromMap));

            // Translation: anchored on the camera. The published alignment places the camera at its
            // VIO-reported Unity-world position regardless of rotation noise, so rotation errors
            // cannot lever-arm the rendered camera away from its true position.
            var translationMeas = translationUnityWorldFromCamera - math.mul(rotationUnityFromEcef, translationEcefFromCamera);

            // Angle between the rotated +Y axis and world +Y. Diagnostic summary of how much
            // pitch+roll the rotation carries away from a gravity-aligned alignment.
            var rotatedUp = math.mul(rotationUnityFromEcef, new double3(0, 1, 0));
            var tiltRadians = math.acos(math.clamp(rotatedUp.y, -1.0, 1.0));

            return new Measurement
            {
                RotationUnityFromEcef = rotationUnityFromEcef,
                Translation = translationMeas,
                TiltRadians = tiltRadians,
            };
        }

        public static Innovation ComputeInnovation(double4x4 currentMean, Matrix<double> sigmaPredicted, double4x4 measurementMean, Matrix<double> sigmaMeas)
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
