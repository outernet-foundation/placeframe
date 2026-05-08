using System;
using ObserveThing;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public static class MakeItSingObservables
    {
        public static IValueObservable<T> ObservableInterpolate<T>(this IValueObservable<T> source, IValueObservable<float> interpolationRate, Func<T, T, bool> checkInterpolationComplete, Func<T, T, float, T> interpolate)
            => new ValueOperator<T>(receiver => new InterpolationObservable<T>(source, interpolationRate, checkInterpolationComplete, interpolate, receiver));

        public static IValueObservable<float> ObservableInterpolate(this IValueObservable<float> source, IValueObservable<float> interpolationRate)
            => source.ObservableInterpolate(interpolationRate, Mathf.Epsilon);

        public static IValueObservable<float> ObservableInterpolate(this IValueObservable<float> source, IValueObservable<float> interpolationRate, float minMagnitude)
            => source.ObservableInterpolate(interpolationRate, (x, y) => Mathf.Abs(x - y) < minMagnitude, (x, y, t) => Mathf.Lerp(x, y, t));

        public static IValueObservable<Vector2> ObservableInterpolate(this IValueObservable<Vector2> source, IValueObservable<float> interpolationRate)
            => source.ObservableInterpolate(interpolationRate, Mathf.Epsilon);

        public static IValueObservable<Vector2> ObservableInterpolate(this IValueObservable<Vector2> source, IValueObservable<float> interpolationRate, float minMagnitude)
            => source.ObservableInterpolate(interpolationRate, (x, y) => (x - y).sqrMagnitude < minMagnitude * minMagnitude, (x, y, t) => Vector2.Lerp(x, y, t));

        public static IValueObservable<Vector3> ObservableInterpolate(this IValueObservable<Vector3> source, IValueObservable<float> interpolationRate)
            => source.ObservableInterpolate(interpolationRate, Mathf.Epsilon);

        public static IValueObservable<Vector3> ObservableInterpolate(this IValueObservable<Vector3> source, IValueObservable<float> interpolationRate, float minMagnitude)
            => source.ObservableInterpolate(interpolationRate, (x, y) => (x - y).sqrMagnitude < minMagnitude * minMagnitude, (x, y, t) => Vector3.Lerp(x, y, t));

        public static IValueObservable<Color> ObservableInterpolate(this IValueObservable<Color> source, IValueObservable<float> interpolationRate)
            => source.ObservableInterpolate(interpolationRate, Mathf.Epsilon);

        public static IValueObservable<Color> ObservableInterpolate(this IValueObservable<Color> source, IValueObservable<float> interpolationRate, float minMagnitude)
            => source.ObservableInterpolate(interpolationRate, (x, y) => ((Vector4)(x - y)).sqrMagnitude < minMagnitude * minMagnitude, (x, y, t) => Color.Lerp(x, y, t));

        public static IValueObservable<Quaternion> ObservableInterpolate(this IValueObservable<Quaternion> source, IValueObservable<float> interpolationRate)
            => source.ObservableInterpolate(interpolationRate, Mathf.Epsilon);

        public static IValueObservable<Quaternion> ObservableInterpolate(this IValueObservable<Quaternion> source, IValueObservable<float> interpolationRate, float minAngle)
            => source.ObservableInterpolate(interpolationRate, (x, y) => Quaternion.Angle(x, y) < minAngle, (x, y, t) => Quaternion.Lerp(x, y, t));
    }
}