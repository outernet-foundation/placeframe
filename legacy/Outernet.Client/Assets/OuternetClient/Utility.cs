using CesiumForUnity;
using Unity.Mathematics;
using UnityEngine;

using System;
using System.Collections.Generic;
using System.Linq;

using FofX.Stateful;
using Outernet.Shared;

namespace Outernet.Client
{
    public static class Utility
    {
        public static Vector3 Flatten(this Vector3 vector3)
        {
            vector3.y = 0;
            return vector3;
        }

        public static Quaternion Flatten(this Quaternion rotation)
        {
            Vector3 forward = rotation * Vector3.forward;
            Vector3 up = rotation * Vector3.up;
            forward.y = 0;
            return Quaternion.LookRotation(forward, up);
        }

        public static bool MagGreaterThan(this Vector3 vector3, float value)
        {
            return vector3.sqrMagnitude > value * value;
        }

        public static bool MagGreaterThanEqualTo(this Vector3 vector3, float value)
        {
            return vector3.sqrMagnitude >= value * value;
        }

        public static bool MagLessThan(this Vector3 vector3, float value)
        {
            return vector3.sqrMagnitude < value * value;
        }

        public static bool MagLessThanEqualTo(this Vector3 vector3, float value)
        {
            return vector3.sqrMagnitude <= value * value;
        }

        public static Color SetAlpha(this Color color, float alpha)
        {
            color.a = alpha;
            return color;
        }

        public static bool TryGetComponentInParent<T>(this Component source, out T component)
        {
            component = source.GetComponentInParent<T>();
            return component != null;
        }

        // Adapted from eastNorthUpToFixedFrame in this file https://github.com/CesiumGS/cesium-native/blob/main/CesiumGeospatial/src/GlobeTransforms.cpp
        public static Quaternion GetEUNRotationFromECEFPosition(double3 ecefPosition)
        {
            var up = CesiumWgs84Ellipsoid.GeodeticSurfaceNormal(ecefPosition);
            var east = math.normalize(new double3(-ecefPosition.y, ecefPosition.x, 0));
            var north = math.cross(up, east);

            // Negatives here are to account for handedness difference
            return Quaternion.LookRotation(-north.ToFloats(), -up.ToFloats());
        }

        public static float Duration(this AnimationCurve curve)
        {
            if (curve.keys.Length == 0)
                return 0;

            return curve.keys[curve.keys.Length - 1].time;
        }

        public static bool RaycastPoint(this Plane plane, Ray ray, out Vector3 point)
        {
            if (plane.Raycast(ray, out var dist))
            {
                point = ray.GetPoint(dist);
                return true;
            }

            point = default;
            return false;
        }

        public static void SetFrom<T>(this ObservableSet<T> set, IEnumerable<T> from)
        {
            if (from == null)
            {
                set.Clear();
                return;
            }

            var missing = set.Except(from).ToArray();
            var added = from.Except(set).ToArray();

            foreach (var toRemove in missing)
                set.Remove(toRemove);

            foreach (var toAdd in added)
                set.Add(toAdd);
        }

        public static void DebugPoint(Vector3 position)
            => DebugPoint(position, 1f, Color.white);

        public static void DebugPoint(Vector3 position, float size)
            => DebugPoint(position, size, Color.white);

        public static void DebugPoint(Vector3 position, Color color)
            => DebugPoint(position, 1f, color);

        public static void DebugPoint(Vector3 position, float size, Color color)
        {
            Debug.DrawRay(position, Vector3.up * 0.5f * size, color);
            Debug.DrawRay(position, Vector3.up * -0.5f * size, color);
            Debug.DrawRay(position, Vector3.right * 0.5f * size, color);
            Debug.DrawRay(position, Vector3.right * -0.5f * size, color);
            Debug.DrawRay(position, Vector3.forward * 0.5f * size, color);
            Debug.DrawRay(position, Vector3.forward * -0.5f * size, color);
        }

        public static Vector3 Position(this Matrix4x4 matrix)
            => (Vector3)matrix.GetColumn(3);

        public static void ExecuteAction<T, TData>(this T node, TData data, Action<TData, T> action, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            where T : IObservableNode => node.ExecuteAction(x => action(data, x), logLevel, postObserverCallback);

        public static void ExecuteAction<T>(this T node, Action<T> action, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            where T : IObservableNode => node.context.ExecuteAction(node, logLevel, postObserverCallback, new DirectAction<T>(action));

        public static void ExecuteActionOrDelay<T, TData>(this T node, TData data, Action<TData, T> action, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            where T : IObservableNode => node.ExecuteActionOrDelay(x => action(data, x), logLevel, postObserverCallback);

        public static void ExecuteActionOrDelay<T>(this T node, Action<T> action, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            where T : IObservableNode => node.context.ExecuteActionOrDelay(node, logLevel, postObserverCallback, new DirectAction<T>(action));

        public static void ScheduleAction<T, TData>(this T node, TData data, Action<TData, T> action, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            where T : IObservableNode => node.ScheduleAction(x => action(data, x), logLevel, postObserverCallback);

        public static void ScheduleAction<T>(this T node, Action<T> action, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            where T : IObservableNode => node.context.ScheduleAction(node, logLevel, postObserverCallback, new DirectAction<T>(action));

        public class DirectAction<T> : ObservableNodeAction<T> where T : IObservableNode
        {
            private Action<T> _action;

            public DirectAction(Action<T> action)
            {
                _action = action;
            }

            public override void Execute(T target)
            {
                _action(target);
            }
        }

        public static void ExecuteAction<T>(this T node, params ObservableNodeAction<T>[] actions)
            where T : IObservableNode => node.context.ExecuteAction(node, default, default, actions);

        public static void ExecuteAction<T>(this T node, Action postObserverCallback, params ObservableNodeAction<T>[] actions)
            where T : IObservableNode => node.context.ExecuteAction(node, default, postObserverCallback, actions);

        public static void ExecuteAction<T>(this T node, FofX.LogLevel logLevel, params ObservableNodeAction<T>[] actions)
            where T : IObservableNode => node.context.ExecuteAction(node, logLevel, default, actions);

        public static void ExecuteAction<T>(this T node, FofX.LogLevel logLevel, Action postObserverCallback, params ObservableNodeAction<T>[] actions)
            where T : IObservableNode => node.context.ExecuteAction(node, logLevel, postObserverCallback, actions);

        public static void ExecuteActionOrDelay<T>(this T node, params ObservableNodeAction<T>[] actions)
            where T : IObservableNode => node.context.ExecuteActionOrDelay(node, default, default, actions);

        public static void ExecuteActionOrDelay<T>(this T node, Action postObserverCallback, params ObservableNodeAction<T>[] actions)
            where T : IObservableNode => node.context.ExecuteActionOrDelay(node, default, postObserverCallback, actions);

        public static void ExecuteActionOrDelay<T>(this T node, FofX.LogLevel logLevel, params ObservableNodeAction<T>[] actions)
            where T : IObservableNode => node.context.ExecuteActionOrDelay(node, logLevel, default, actions);

        public static void ExecuteActionOrDelay<T>(this T node, FofX.LogLevel logLevel, Action postObserverCallback, params ObservableNodeAction<T>[] actions)
            where T : IObservableNode => node.context.ExecuteActionOrDelay(node, logLevel, postObserverCallback, actions);

        public static void ScheduleAction<T>(this T node, params ObservableNodeAction<T>[] actions)
            where T : IObservableNode => node.context.ScheduleAction(node, default, default, actions);

        public static void ScheduleAction<T>(this T node, Action postObserverCallback, params ObservableNodeAction<T>[] actions)
            where T : IObservableNode => node.context.ScheduleAction(node, default, postObserverCallback, actions);

        public static void ScheduleAction<T>(this T node, FofX.LogLevel logLevel, params ObservableNodeAction<T>[] actions)
            where T : IObservableNode => node.context.ScheduleAction(node, logLevel, default, actions);

        public static void ScheduleAction<T>(this T node, FofX.LogLevel logLevel, Action postObserverCallback, params ObservableNodeAction<T>[] actions)
            where T : IObservableNode => node.context.ScheduleAction(node, logLevel, postObserverCallback, actions);

        public static void ExecuteSet<T>(this ObservablePrimitive<T> primitive, T value, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            => primitive.ExecuteAction(logLevel, postObserverCallback, new SetPrimitiveValueAction<T>(value));

        public static void ExecuteSetOrDelay<T>(this ObservablePrimitive<T> primitive, T value, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            => primitive.ExecuteActionOrDelay(logLevel, postObserverCallback, new SetPrimitiveValueAction<T>(value));

        public static void ScheduleSet<T>(this ObservablePrimitive<T> primitive, T value, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            => primitive.ScheduleAction(logLevel, postObserverCallback, new SetPrimitiveValueAction<T>(value));

        public static void ExecuteAdd<T>(this ObservableSet<T> primitive, T value, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            => primitive.ExecuteAction(logLevel, postObserverCallback, new AddValueToSetAction<T>(value));

        public static void ExecuteAddOrDelay<T>(this ObservableSet<T> primitive, T value, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            => primitive.ExecuteActionOrDelay(logLevel, postObserverCallback, new AddValueToSetAction<T>(value));

        public static void ScheduleAdd<T>(this ObservableSet<T> primitive, T value, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            => primitive.ScheduleAction(logLevel, postObserverCallback, new AddValueToSetAction<T>(value));

        public static void ExecuteRemove<T>(this ObservableSet<T> primitive, T value, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            => primitive.ExecuteAction(logLevel, postObserverCallback, new RemoveValueFromSetAction<T>(value));

        public static void ExecuteRemoveOrDelay<T>(this ObservableSet<T> primitive, T value, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            => primitive.ExecuteActionOrDelay(logLevel, postObserverCallback, new RemoveValueFromSetAction<T>(value));

        public static void ScheduleRemove<T>(this ObservableSet<T> primitive, T value, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            => primitive.ScheduleAction(logLevel, postObserverCallback, new RemoveValueFromSetAction<T>(value));

        public static void ExecuteSet<T>(this ObservableSet<T> primitive, T[] values, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            => primitive.ExecuteAction(logLevel, postObserverCallback, new SetValuesInSetAction<T>(values));

        public static void ExecuteSetOrDelay<T>(this ObservableSet<T> primitive, T[] values, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            => primitive.ExecuteActionOrDelay(logLevel, postObserverCallback, new SetValuesInSetAction<T>(values));

        public static void ScheduleSet<T>(this ObservableSet<T> primitive, T[] values, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            => primitive.ScheduleAction(logLevel, postObserverCallback, new SetValuesInSetAction<T>(values));

        public static void ExecuteAdd<TKey, TValue>(this ObservableDictionary<TKey, TValue> dictionary, TKey key, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            where TValue : IObservableNode, new() => dictionary.ExecuteAction(logLevel, postObserverCallback, new AddKeyToDictionaryAction<TKey, TValue>(key));

        public static void ExecuteAddOrDelay<TKey, TValue>(this ObservableDictionary<TKey, TValue> dictionary, TKey key, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            where TValue : IObservableNode, new() => dictionary.ExecuteActionOrDelay(logLevel, postObserverCallback, new AddKeyToDictionaryAction<TKey, TValue>(key));

        public static void ScheduleAdd<TKey, TValue>(this ObservableDictionary<TKey, TValue> dictionary, TKey key, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            where TValue : IObservableNode, new() => dictionary.ScheduleAction(logLevel, postObserverCallback, new AddKeyToDictionaryAction<TKey, TValue>(key));

        public static void ExecuteRemove<TKey, TValue>(this ObservableDictionary<TKey, TValue> dictionary, TKey key, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            where TValue : IObservableNode, new() => dictionary.ExecuteAction(logLevel, postObserverCallback, new RemoveKeyFromDictionaryAction<TKey, TValue>(key));

        public static void ExecuteRemoveOrDelay<TKey, TValue>(this ObservableDictionary<TKey, TValue> dictionary, TKey key, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            where TValue : IObservableNode, new() => dictionary.ExecuteActionOrDelay(logLevel, postObserverCallback, new RemoveKeyFromDictionaryAction<TKey, TValue>(key));

        public static void ScheduleRemove<TKey, TValue>(this ObservableDictionary<TKey, TValue> dictionary, TKey key, FofX.LogLevel logLevel = FofX.LogLevel.Debug, Action postObserverCallback = default)
            where TValue : IObservableNode, new() => dictionary.ScheduleAction(logLevel, postObserverCallback, new RemoveKeyFromDictionaryAction<TKey, TValue>(key));

        public static Double3 ToRecord(this double3 source)
        {
            return new Double3(source.x, source.y, source.z);
        }

        public static double3 ToMathematicsDouble3(this Double3 source)
        {
            return new double3(source.x, source.y, source.z);
        }

        // public static (Vector3 position, Quaternion rotation) EcefToLocal(double4x4 ecefToLocalTransform, double3 position, quaternion rotation)
        // {
        //     var ecefTransformMatrix = Double4x4.FromTranslationRotation(position, rotation);
        //     var localTransformMatrix = math.mul(ecefToLocalTransform, ecefTransformMatrix);
        //     return (
        //         // Also see Localizer.cs 
        //         //
        //         // I never worked out why this position inversion (and the one in
        //         // SetEcefTransformFromLocalTransform, and the two other ones in Localizer.cs) are
        //         // required. I just brute-force guess-and-checked until I found something that worked.
        //         // The ecef rotations for localization maps comes from Cesium, and I searched
        //         // CesiumForUnity and Cesium-Native for answers, but there are many layers of
        //         // indirection, and at time of of writing, all origin modes go through a EUN (East-Up-North)
        //         // coordinate system that I believe gets "undone" by the local Unity transform of the
        //         // CesiumGeoreference itself. When I realized that, I gave up. But the ultimate
        //         // result, apparently, is that the required transform to go from ecef space to unity
        //         // space happens to be a position inversion. ¯\_(ツ)_/¯ 
        //         //
        //         // Apologies to the poor soul (probably me) who has to maintain this code in the future.
        //         -localTransformMatrix.Position().ToFloats(),
        //         localTransformMatrix.Rotation()
        //     );
        // }

        // public static (double3 position, quaternion rotation) LocalToEcef(double4x4 localToEcefTransform, Vector3 position, Quaternion rotation)
        // {
        //     var localTransformMatrix = Double4x4.FromTranslationRotation(
        //         // See above
        //         -position.ToDoubles(),
        //         rotation);
        //     var ecefTransformMatrix = math.mul(localToEcefTransform, localTransformMatrix);
        //     return (ecefTransformMatrix.Position(), ecefTransformMatrix.Rotation());
        // }
    }
}