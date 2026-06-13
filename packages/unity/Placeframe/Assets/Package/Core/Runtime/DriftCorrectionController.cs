using Unity.Mathematics;

namespace Placeframe.Core
{
    // The published reference frame and the control law that moves it. VIO is authoritative between
    // corrections: the frame holds steady and re-anchors to the filter's best estimate only when that
    // estimate diverges past a deadband — one that starts wide and shrinks toward a floor as the device
    // moves and, more slowly, as time passes, resetting to wide on any correction. A correction eases the
    // frame to the estimate over a short fixed duration — never a snap. Bootstrap and operator override
    // set the frame outright.
    public sealed class DriftCorrectionController
    {
        public double4x4 Current { get; private set; } = double4x4.identity;
        public double4x4 CurrentInverse { get; private set; } = double4x4.identity;

        private double _metersWalked;
        private double _radiansTurned;
        private float _lastCorrectionTime;
        private double3 _lastVioPosition;
        private quaternion _lastVioRotation;
        private bool _hasVioReference;

        private bool _slewing;
        private double4x4 _slewStart;
        private double4x4 _slewTarget;
        private float _slewElapsed;

        public void Set(double4x4 target, float nowSeconds)
        {
            Current = target;
            CurrentInverse = math.inverse(target);
            _slewing = false;
            ResetCorrectionReference(nowSeconds);

            VisualPositioningSystem.LogDebug("step=reloc.frame action=set " + PositionFields("set", target.Position()));
        }

        public bool Observe(double4x4 bestEstimate, double3 vioPosition, quaternion vioRotation, float nowSeconds)
        {
            AccumulateMotion(vioPosition, vioRotation);

            var seconds = nowSeconds - _lastCorrectionTime;
            var translationThreshold = Threshold(
                RelocalizationConfig.CorrectionTranslationMaxMeters,
                RelocalizationConfig.CorrectionTranslationMinMeters,
                (_metersWalked / RelocalizationConfig.CorrectionDistanceToMinMeters) + (seconds / RelocalizationConfig.CorrectionTimeToMinSeconds)
            );
            var rotationThreshold = Threshold(
                RelocalizationConfig.CorrectionRotationMaxRadians,
                RelocalizationConfig.CorrectionRotationMinRadians,
                (_radiansTurned / RelocalizationConfig.CorrectionAngleToMinRadians) + (seconds / RelocalizationConfig.CorrectionTimeToMinSeconds)
            );

            var residual = Se3.Log(math.mul(CurrentInverse, bestEstimate));
            var residualRadians = math.length(new double3(residual[0], residual[1], residual[2]));
            var residualMeters = math.length(new double3(residual[3], residual[4], residual[5]));
            var deadbandFields = DeadbandFields(residualMeters, residualRadians, translationThreshold, rotationThreshold, _metersWalked, _radiansTurned, seconds);

            if (residualMeters <= translationThreshold && residualRadians <= rotationThreshold)
            {
                VisualPositioningSystem.LogDebug("step=reloc.frame action=hold " + deadbandFields);
                return false;
            }

            // Re-anchor: ease the frame to the best estimate from where it sits now, and reset the
            // deadband to its widest so the next correction has to re-earn divergence from scratch.
            VisualPositioningSystem.LogDebug(
                "step=reloc.frame action=correct " + deadbandFields
                    + " " + PositionFields("from", Current.Position())
                    + " " + PositionFields("to", bestEstimate.Position())
            );

            _slewStart = Current;
            _slewTarget = bestEstimate;
            _slewElapsed = 0f;
            _slewing = true;
            ResetCorrectionReference(nowSeconds);
            return true;
        }

        public bool Advance(float deltaSeconds)
        {
            if (!_slewing || deltaSeconds <= 0f)
                return false;

            _slewElapsed += deltaSeconds;
            var t = math.saturate(_slewElapsed / RelocalizationConfig.CorrectionSlewSeconds);
            var eased = t * t * (3f - (2f * t));
            Current = Double4x4.Interpolate(_slewStart, _slewTarget, eased);
            CurrentInverse = math.inverse(Current);

            if (t >= 1f)
            {
                _slewing = false;
                VisualPositioningSystem.LogDebug("step=reloc.frame action=slewDone " + PositionFields("at", Current.Position()));
            }

            return true;
        }

        private void AccumulateMotion(double3 vioPosition, quaternion vioRotation)
        {
            if (_hasVioReference)
            {
                _metersWalked += math.length(vioPosition - _lastVioPosition);
                var alignment = math.abs(math.dot(_lastVioRotation.value, vioRotation.value));
                _radiansTurned += 2.0 * math.acos(math.clamp((double)alignment, 0.0, 1.0));
            }

            _lastVioPosition = vioPosition;
            _lastVioRotation = vioRotation;
            _hasVioReference = true;
        }

        private void ResetCorrectionReference(float nowSeconds)
        {
            _metersWalked = 0.0;
            _radiansTurned = 0.0;
            _lastCorrectionTime = nowSeconds;
            _hasVioReference = false;
        }

        private static double Threshold(double max, double min, double progress) => math.lerp(max, min, math.saturate(progress));

        private static string DeadbandFields(
            double residualMeters,
            double residualRadians,
            double translationThreshold,
            double rotationThreshold,
            double metersWalked,
            double radiansTurned,
            double seconds
        ) =>
            $"residM={residualMeters:F3} residRad={residualRadians:F4} transThresh={translationThreshold:F3}"
                + $" rotThresh={rotationThreshold:F4} walked={metersWalked:F3} turned={radiansTurned:F4} since={seconds:F1}";

        private static string PositionFields(string prefix, double3 position) =>
            $"{prefix}Tx={position.x:F3} {prefix}Ty={position.y:F3} {prefix}Tz={position.z:F3}";
    }
}
