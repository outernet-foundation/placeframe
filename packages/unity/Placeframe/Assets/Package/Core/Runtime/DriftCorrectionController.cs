using Unity.Mathematics;

namespace Placeframe.Core
{
    // The published reference frame and the control law that moves it. VIO is authoritative between
    // corrections: the frame holds steady and re-anchors to the filter's best estimate only when that
    // estimate diverges past a deadband — one that starts wide and shrinks toward a floor as the device
    // moves and, more slowly, as time passes, resetting to wide on any correction. A correction eases the
    // frame to the estimate over a short fixed duration — never a snap. Bootstrap and operator override
    // set the frame outright.
    //
    // The control law runs on a raw-VIO-anchored base frame. The published frame adds an online
    // scale-compensation offset on top: the device's tracker under-reports motion by a roughly constant
    // factor, so the published content is shifted by (1 - 1/ema) of the distance walked since the last
    // re-anchor, which keeps rendered camera-to-content distances metric between corrections. The factor
    // is an EMA of the filter's per-segment scaleRatio, so it self-tunes per device. The offset never
    // enters the residual, so it cannot inflate the deadband or change correction frequency.
    public sealed class DriftCorrectionController
    {
        private double4x4 _base = double4x4.identity;

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

        private double _scaleEma = 1.0;
        private int _scaleSamples;
        private double3 _compAnchorVio;
        private double3 _offsetTarget;
        private double3 _offsetPublished;

        public void Set(double4x4 target, double3 vioPosition, float nowSeconds)
        {
            _base = target;
            _compAnchorVio = vioPosition;
            _offsetTarget = double3.zero;
            _offsetPublished = double3.zero;
            _slewing = false;
            ResetCorrectionReference(nowSeconds);
            Republish();

            VisualPositioningSystem.LogDebug("step=reloc.frame action=set " + PositionFields("set", target.Position()));
        }

        public bool Observe(double4x4 bestEstimate, double3 vioPosition, quaternion vioRotation, double? scaleRatio, float nowSeconds)
        {
            AccumulateMotion(vioPosition, vioRotation);

            UpdateScaleEma(scaleRatio);
            var biasInverse = BiasInverse();
            _offsetTarget = ClampOffset((1.0 - biasInverse) * (vioPosition - _compAnchorVio));
            VisualPositioningSystem.LogDebug(ScaleFields(scaleRatio, biasInverse));

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

            // The residual is measured against the raw base, not the published (offset-inclusive) frame,
            // so the scale offset never registers as drift and never drives a correction.
            var baseInverse = math.inverse(_base);
            var residual = Se3.Log(math.mul(baseInverse, bestEstimate));
            var residualRadians = math.length(new double3(residual[0], residual[1], residual[2]));
            var residualMeters = math.length(new double3(residual[3], residual[4], residual[5]));
            var deadbandFields = DeadbandFields(residualMeters, residualRadians, translationThreshold, rotationThreshold, _metersWalked, _radiansTurned, seconds);
            var compFields = CompFrameFields(vioPosition, biasInverse);

            if (residualMeters <= translationThreshold && residualRadians <= rotationThreshold)
            {
                VisualPositioningSystem.LogDebug("step=reloc.frame action=hold " + deadbandFields + " " + compFields);
                return false;
            }

            // Re-anchor: ease the base to the best estimate from where it sits now, and reset the
            // deadband to its widest so the next correction has to re-earn divergence from scratch. The
            // compensation anchor resets too, so the offset target collapses to zero and eases down over
            // the same window — the published frame stays continuous across the re-anchor.
            VisualPositioningSystem.LogDebug(
                "step=reloc.frame action=correct " + deadbandFields + " " + compFields
                    + " " + PositionFields("from", _base.Position())
                    + " " + PositionFields("to", bestEstimate.Position())
            );

            _slewStart = _base;
            _slewTarget = bestEstimate;
            _slewElapsed = 0f;
            _slewing = true;
            _compAnchorVio = vioPosition;
            _offsetTarget = double3.zero;
            ResetCorrectionReference(nowSeconds);
            return true;
        }

        public bool Advance(float deltaSeconds)
        {
            if (deltaSeconds <= 0f)
                return false;

            var changed = false;

            if (_slewing)
            {
                _slewElapsed += deltaSeconds;
                var t = math.saturate(_slewElapsed / RelocalizationConfig.CorrectionSlewSeconds);
                var eased = t * t * (3f - (2f * t));
                _base = Double4x4.Interpolate(_slewStart, _slewTarget, eased);
                changed = true;

                if (t >= 1f)
                {
                    _slewing = false;
                    VisualPositioningSystem.LogDebug("step=reloc.frame action=slewDone " + PositionFields("at", _base.Position()));
                }
            }

            // The offset target is set at localization cadence; ease the published offset toward it each
            // frame so it tracks smoothly between measurements.
            var offsetEase = math.saturate(deltaSeconds / RelocalizationConfig.CompOffsetEaseSeconds);
            var newOffset = math.lerp(_offsetPublished, _offsetTarget, offsetEase);

            if (math.any(newOffset != _offsetPublished))
            {
                _offsetPublished = newOffset;
                changed = true;
            }

            if (changed)
                Republish();

            return changed;
        }

        private void Republish()
        {
            Current = ComposeOffset(_base, _offsetPublished);
            CurrentInverse = math.inverse(Current);
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

        // Fold one per-segment scale ratio into the EMA. Null (standstill / no matched segment) and
        // out-of-band ratios (VIO jumps) are ignored, so a glitch cannot poison the estimate.
        private void UpdateScaleEma(double? scaleRatio)
        {
            if (scaleRatio is not double ratio)
                return;

            if (ratio < RelocalizationConfig.CompScaleRatioMin || ratio > RelocalizationConfig.CompScaleRatioMax)
                return;

            _scaleEma = _scaleSamples == 0 ? ratio : math.lerp(_scaleEma, ratio, RelocalizationConfig.CompEmaAlpha);
            _scaleSamples++;
        }

        // The metric scale factor applied to VIO displacement: 1 / ema once warmed and past the
        // deadband, else identity (no offset). Disabled platforms return identity, which routes the
        // offset to zero without a separate unreachable branch.
        private double BiasInverse()
        {
            var warmed = _scaleSamples >= RelocalizationConfig.CompWarmupSamples;
            var beyondDeadzone = math.abs(1.0 - _scaleEma) > RelocalizationConfig.CompDeadzone;
            var active = RelocalizationConfig.CompEnabled && warmed && beyondDeadzone;
            return active ? 1.0 / _scaleEma : 1.0;
        }

        private static double3 ClampOffset(double3 offset)
        {
            var length = math.length(offset);
            return length > RelocalizationConfig.CompMaxOffsetMeters
                ? offset * (RelocalizationConfig.CompMaxOffsetMeters / length)
                : offset;
        }

        private static double4x4 ComposeOffset(double4x4 baseFrame, double3 offset)
        {
            var result = baseFrame;
            result.c3 = new double4(result.c3.xyz + offset, result.c3.w);
            return result;
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

        private string ScaleFields(double? scaleRatio, double biasInverse)
        {
            var sample = scaleRatio.HasValue ? scaleRatio.Value.ToString("F3") : "null";
            var inBand =
                scaleRatio is double ratio
                && ratio >= RelocalizationConfig.CompScaleRatioMin
                && ratio <= RelocalizationConfig.CompScaleRatioMax;
            return $"step=reloc.scale sample={sample} inBand={inBand} ema={_scaleEma:F4} samples={_scaleSamples} biasInverse={biasInverse:F4}";
        }

        private string CompFrameFields(double3 vioPosition, double biasInverse) =>
            $"offsetMag={math.length(_offsetPublished):F3} offsetTargetMag={math.length(_offsetTarget):F3}"
                + $" anchorDist={math.length(vioPosition - _compAnchorVio):F3} biasInverse={biasInverse:F4}";

        private static string PositionFields(string prefix, double3 position) =>
            $"{prefix}Tx={position.x:F3} {prefix}Ty={position.y:F3} {prefix}Tz={position.z:F3}";
    }
}
