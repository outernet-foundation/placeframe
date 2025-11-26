using System;
using System.Threading;

using UnityEngine;
using Cysharp.Threading.Tasks;

namespace Outernet.MapRegistrationTool
{
    public static class Tween
    {
        public static UniTask Curve<T>(T fromValue, T toValue, Func<T, T, float, T> interpolate, AnimationCurve curve, Action<T> apply, CancellationToken token = default)
            => Curve(fromValue, toValue, interpolate, curve, curve.Duration(), apply, token);

        public static async UniTask Curve<T>(T fromValue, T toValue, Func<T, T, float, T> interpolate, AnimationCurve curve, float duration, Action<T> apply, CancellationToken token = default)
        {
            float time = 0;
            float curveDuration = curve.Duration();

            while (time < duration)
            {
                apply(interpolate(fromValue, toValue, curve.Evaluate((time / duration) * curveDuration)));
                await UniTask.Yield(PlayerLoopTiming.LastPostLateUpdate);
                token.ThrowIfCancellationRequested();
                time += Time.deltaTime;
            }

            apply(toValue);
        }

        public static async UniTask Linear<T>(T fromValue, T toValue, Func<T, T, float, T> interpolate, float duration, Action<T> apply, CancellationToken token = default)
        {
            float time = 0;

            while (time < duration)
            {
                apply(interpolate(fromValue, toValue, time / duration));
                await UniTask.Yield(PlayerLoopTiming.LastPostLateUpdate);
                token.ThrowIfCancellationRequested();
                time += Time.deltaTime;
            }

            apply(toValue);
        }

        public static UniTask FloatEaseInOut(float fromValue, float toValue, Action<float> apply, CancellationToken token = default)
            => FloatEaseInOut(fromValue, toValue, Mathf.Abs(fromValue - toValue), apply, token);

        public static UniTask FloatEaseInOut(float fromValue, float toValue, float duration, Action<float> apply, CancellationToken token = default)
            => Float(fromValue, toValue, AnimationCurve.EaseInOut(0, 0, duration, 1), apply, token);

        public static UniTask Float(float fromValue, float toValue, Action<float> apply, CancellationToken token = default)
            => Float(fromValue, toValue, Mathf.Abs(fromValue - toValue), apply, token);

        public static UniTask Float(float fromValue, float toValue, float duration, Action<float> apply, CancellationToken token = default)
            => Linear(fromValue, toValue, Mathf.Lerp, duration, apply, token);

        public static UniTask Float(float fromValue, float toValue, AnimationCurve curve, Action<float> apply, CancellationToken token = default)
            => Curve(fromValue, toValue, Mathf.Lerp, curve, apply, token);
    }
}