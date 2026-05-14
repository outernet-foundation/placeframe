using System;
using ObserveThing;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public static class MakeItSingObservables
    {
        public static IValueObservable<T> ObservableNetworkSmooth<T>(this IValueObservable<T> source, IValueObservable<float> interpolationRate, IValueObservable<AnimationCurve> curve, Func<T, T, float> calcDelta, Func<T, T, float, T> interpolate)
            => new ValueOperator<T>(receiver => new NetworkSmoothObservable<T>(source, interpolationRate ?? new ObservableValue<float>(1f), curve ?? new ObservableValue<AnimationCurve>(value: null), calcDelta, interpolate, receiver));

        public static IValueObservable<float> ObservableNetworkSmooth(this IValueObservable<float> source, IValueObservable<float> interpolationRate = default, IValueObservable<AnimationCurve> curve = default)
            => source.ObservableNetworkSmooth(interpolationRate, curve, (x, y) => Mathf.Abs(x - y), (x, y, t) => Mathf.Lerp(x, y, t));

        public static IValueObservable<Vector2> ObservableNetworkSmooth(this IValueObservable<Vector2> source, IValueObservable<float> interpolationRate = default, IValueObservable<AnimationCurve> curve = default)
            => source.ObservableNetworkSmooth(interpolationRate, curve, (x, y) => (x - y).sqrMagnitude, (x, y, t) => Vector2.Lerp(x, y, t));

        public static IValueObservable<Vector3> ObservableNetworkSmooth(this IValueObservable<Vector3> source, IValueObservable<float> interpolationRate = default, IValueObservable<AnimationCurve> curve = default)
            => source.ObservableNetworkSmooth(interpolationRate, curve, (x, y) => (x - y).sqrMagnitude, (x, y, t) => Vector3.Lerp(x, y, t));

        public static IValueObservable<Color> ObservableNetworkSmooth(this IValueObservable<Color> source, IValueObservable<float> interpolationRate = default, IValueObservable<AnimationCurve> curve = default)
            => source.ObservableNetworkSmooth(interpolationRate, curve, (x, y) => ((Vector4)(x - y)).sqrMagnitude, (x, y, t) => Color.Lerp(x, y, t));

        public static IValueObservable<Quaternion> ObservableNetworkSmooth(this IValueObservable<Quaternion> source, IValueObservable<float> interpolationRate = default, IValueObservable<AnimationCurve> curve = default)
            => source.ObservableNetworkSmooth(interpolationRate, curve, (x, y) => Quaternion.Angle(x, y), (x, y, t) => Quaternion.Slerp(x, y, t));

        public static IValueObservable<T> ObservableInterpolate<T>(this IValueObservable<T> source, IValueObservable<float> interpolationRate, IValueObservable<AnimationCurve> curve, Func<T, T, float> calcDelta, Func<T, T, float, T> interpolate)
            => new ValueOperator<T>(receiver => new InterpolationObservable<T>(source, interpolationRate ?? new ObservableValue<float>(1f), curve ?? new ObservableValue<AnimationCurve>(value: null), calcDelta, interpolate, receiver));

        public static IValueObservable<float> ObservableInterpolate(this IValueObservable<float> source, IValueObservable<float> interpolationRate = default, IValueObservable<AnimationCurve> curve = default)
            => source.ObservableInterpolate(interpolationRate, curve, (x, y) => Mathf.Abs(x - y), (x, y, t) => Mathf.Lerp(x, y, t));

        public static IValueObservable<Vector2> ObservableInterpolate(this IValueObservable<Vector2> source, IValueObservable<float> interpolationRate = default, IValueObservable<AnimationCurve> curve = default)
            => source.ObservableInterpolate(interpolationRate, curve, (x, y) => (x - y).sqrMagnitude, (x, y, t) => Vector2.Lerp(x, y, t));

        public static IValueObservable<Vector3> ObservableInterpolate(this IValueObservable<Vector3> source, IValueObservable<float> interpolationRate = default, IValueObservable<AnimationCurve> curve = default)
            => source.ObservableInterpolate(interpolationRate, curve, (x, y) => (x - y).sqrMagnitude, (x, y, t) => Vector3.Lerp(x, y, t));

        public static IValueObservable<Color> ObservableInterpolate(this IValueObservable<Color> source, IValueObservable<float> interpolationRate = default, IValueObservable<AnimationCurve> curve = default)
            => source.ObservableInterpolate(interpolationRate, curve, (x, y) => ((Vector4)(x - y)).sqrMagnitude, (x, y, t) => Color.Lerp(x, y, t));

        public static IValueObservable<Quaternion> ObservableInterpolate(this IValueObservable<Quaternion> source, IValueObservable<float> interpolationRate = default, IValueObservable<AnimationCurve> curve = default)
            => source.ObservableInterpolate(interpolationRate, curve, (x, y) => Quaternion.Angle(x, y), (x, y, t) => Quaternion.Slerp(x, y, t));
    }
}