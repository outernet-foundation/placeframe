using System;
using System.Threading;
using Cysharp.Threading.Tasks;
using Unity.Mathematics;
using UnityEngine;

public static class Interpolation
{
    public delegate T InterpolationDelegate<T>(T from, T to, float time);

    public static UniTask Run(Quaternion from, Quaternion to, AnimationCurve curve, Action<Quaternion> callback, CancellationToken cancellationToken = default)
        => Run(from, to, curve, Quaternion.LerpUnclamped, callback, cancellationToken);

    public static UniTask Run(Quaternion from, Quaternion to, AnimationCurve curve, float speed, Action<Quaternion> callback, CancellationToken cancellationToken = default)
        => Run(from, to, curve, speed, Quaternion.LerpUnclamped, callback, cancellationToken);

    public static UniTask Run(Quaternion from, Quaternion to, float duration, Action<Quaternion> callback, CancellationToken cancellationToken = default)
        => Run(from, to, duration, Quaternion.Lerp, callback, cancellationToken);

    public static UniTask Run(Vector4 from, Vector4 to, AnimationCurve curve, Action<Vector4> callback, CancellationToken cancellationToken = default)
        => Run(from, to, curve, Vector4.LerpUnclamped, callback, cancellationToken);

    public static UniTask Run(Vector4 from, Vector4 to, AnimationCurve curve, float speed, Action<Vector4> callback, CancellationToken cancellationToken = default)
        => Run(from, to, curve, speed, Vector4.LerpUnclamped, callback, cancellationToken);

    public static UniTask Run(Vector4 from, Vector4 to, float duration, Action<Vector4> callback, CancellationToken cancellationToken = default)
        => Run(from, to, duration, Vector4.Lerp, callback, cancellationToken);

    public static UniTask Run(Vector3 from, Vector3 to, AnimationCurve curve, Action<Vector3> callback, CancellationToken cancellationToken = default)
        => Run(from, to, curve, Vector3.LerpUnclamped, callback, cancellationToken);

    public static UniTask Run(Vector3 from, Vector3 to, AnimationCurve curve, float speed, Action<Vector3> callback, CancellationToken cancellationToken = default)
        => Run(from, to, curve, speed, Vector3.LerpUnclamped, callback, cancellationToken);

    public static UniTask Run(Vector3 from, Vector3 to, float duration, Action<Vector3> callback, CancellationToken cancellationToken = default)
        => Run(from, to, duration, Vector3.Lerp, callback, cancellationToken);

    public static UniTask Run(Vector2 from, Vector2 to, AnimationCurve curve, Action<Vector2> callback, CancellationToken cancellationToken = default)
        => Run(from, to, curve, Vector2.LerpUnclamped, callback, cancellationToken);

    public static UniTask Run(Vector2 from, Vector2 to, AnimationCurve curve, float speed, Action<Vector2> callback, CancellationToken cancellationToken = default)
        => Run(from, to, curve, speed, Vector2.LerpUnclamped, callback, cancellationToken);

    public static UniTask Run(Vector2 from, Vector2 to, float duration, Action<Vector2> callback, CancellationToken cancellationToken = default)
        => Run(from, to, duration, Vector2.Lerp, callback, cancellationToken);

    public static UniTask Run01(AnimationCurve curve, Action<float> callback, CancellationToken cancellationToken = default)
        => Run(0f, 1f, curve, Mathf.LerpUnclamped, callback, cancellationToken);

    public static UniTask Run01(AnimationCurve curve, float speed, Action<float> callback, CancellationToken cancellationToken = default)
        => Run(0f, 1f, curve, speed, Mathf.LerpUnclamped, callback, cancellationToken);

    public static UniTask Run01(float duration, Action<float> callback, CancellationToken cancellationToken = default)
        => Run(0f, 1f, duration, callback, cancellationToken);

    public static UniTask Run(float from, float to, AnimationCurve curve, Action<float> callback, CancellationToken cancellationToken = default)
        => Run(from, to, curve, Mathf.LerpUnclamped, callback, cancellationToken);

    public static UniTask Run(float from, float to, AnimationCurve curve, float speed, Action<float> callback, CancellationToken cancellationToken = default)
        => Run(from, to, curve, speed, Mathf.LerpUnclamped, callback, cancellationToken);

    public static UniTask Run(float from, float to, float duration, Action<float> callback, CancellationToken cancellationToken = default)
        => Run(from, to, duration, Mathf.Lerp, callback, cancellationToken);

    public static UniTask Run<T>(T from, T to, AnimationCurve curve, InterpolationDelegate<T> interpolate, Action<T> callback, CancellationToken cancellationToken = default)
        => Run(from, to, curve, 1f, interpolate, callback, cancellationToken);

    public static UniTask Run<T>(T from, T to, AnimationCurve curve, float speed, InterpolationDelegate<T> interpolate, Action<T> callback, CancellationToken cancellationToken = default)
        => Run(0, curve[curve.keys.Length - 1].time, curve[curve.keys.Length - 1].time / speed, Mathf.LerpUnclamped, x => callback(interpolate(from, to, curve.Evaluate(x * speed))), cancellationToken);

    public static async UniTask Run<T>(T from, T to, float duration, InterpolationDelegate<T> interpolate, Action<T> callback, CancellationToken cancellationToken)
    {
        float elapsed = 0;
        cancellationToken.ThrowIfCancellationRequested();

        while (elapsed <= duration)
        {
            callback(interpolate(from, to, elapsed));
            await UniTask.WaitForEndOfFrame(cancellationToken);
            elapsed += Time.deltaTime;
        }

        callback(to);
    }
}