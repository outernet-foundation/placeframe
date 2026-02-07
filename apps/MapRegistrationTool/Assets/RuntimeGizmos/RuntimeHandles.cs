using System;
using UnityEngine;
using FofX.Stateful;

namespace Placeframe.MapRegistrationTool
{
    public static class RuntimeHandles
    {
        public static bool RaycastCylinder(Ray ray, Vector3 origin, Vector3 normal, float height, float radius, out float distance)
        {
            normal = normal.normalized;

            bool hitCylinder = false;
            float minDist = float.MaxValue;

            if (new Plane(normal, origin + (normal * height)).Raycast(ray, out float enterTop))
            {
                var delta = ray.GetPoint(enterTop) - (origin + (normal * height));
                if (delta.MagLessThanEqualTo(radius))
                {
                    hitCylinder = true;
                    minDist = enterTop;
                }
            }

            if (new Plane(-normal, origin).Raycast(ray, out float enterBottom))
            {
                var delta = ray.GetPoint(enterBottom) - origin;
                if (delta.MagLessThanEqualTo(radius))
                {
                    hitCylinder = true;
                    minDist = Mathf.Min(enterBottom, minDist);
                }
            }

            var toLocalSpace = Matrix4x4.TRS(origin, Quaternion.LookRotation(normal), Vector3.one).inverse;

            var localRayOrigin = toLocalSpace.MultiplyPoint(ray.origin);
            var localRayDirection = toLocalSpace.MultiplyVector(ray.direction);

            var projectedOrigin = new Vector3(localRayOrigin.x, localRayOrigin.y, 0);
            var projectedDirection = new Vector3(localRayDirection.x, localRayDirection.y, 0).normalized;

            if (Vector3.Dot(projectedDirection, -projectedOrigin.normalized) > 0)
            {
                var U = -projectedOrigin;
                var U1 = Vector3.Project(U, projectedDirection);
                var U2 = U - U1;
                var d = U2.magnitude;

                if (d < radius)
                {
                    var m = Mathf.Sqrt(radius * radius - d * d);
                    var point = projectedOrigin + U1 - m * projectedDirection;

                    var t = localRayDirection.x != 0 ?
                        (point.x - localRayOrigin.x) / localRayDirection.x :
                        (point.y - localRayOrigin.y) / localRayDirection.y;

                    var z = localRayOrigin.z + localRayDirection.z * t;

                    if (z > 0 && z < height)
                    {
                        point.z = z;
                        hitCylinder = true;
                        minDist = Mathf.Min(minDist, (ray.origin - toLocalSpace.inverse.MultiplyPoint(point)).magnitude);
                    }
                }
            }

            if (hitCylinder)
            {
                distance = minDist;
                return true;
            }

            distance = float.MaxValue;
            return false;
        }

        public static bool RaycastCircle(Ray ray, Vector3 center, Vector3 normal, float radius, float padding, out float distance)
        {
            if (RaycastCylinder(ray, center - (normal * padding), normal, padding * 2f, radius + padding, out distance))
            {
                var localIntersect = Matrix4x4.TRS(center, Quaternion.LookRotation(normal), Vector3.one).inverse.MultiplyPoint3x4(ray.GetPoint(distance));
                localIntersect.z = 0;
                return localIntersect.MagGreaterThanEqualTo(radius - padding);
            }

            distance = 0;
            return false;
        }

        public static bool RaycastSphere(Ray ray, Vector3 center, float radius, out float distance)
        {
            Vector3 L = center - ray.origin;
            float tca = Vector3.Dot(L, ray.direction);

            if (tca < 0)
            {
                distance = 0;
                return false;
            }

            float d2 = Vector3.Dot(L, L) - tca * tca;

            if (d2 > radius * radius)
            {
                distance = 0;
                return false;
            }

            float thc = Mathf.Sqrt(radius * radius - d2);
            distance = tca - thc;
            return true;
        }

        public static SliderHandle SliderHandle(Vector3 direction = default, float length = 1f, Vector3 position = default, Quaternion? rotation = default, float scale = 1f, Color? color = default, Func<SliderHandle.Props, IDisposable> binding = default)
        {
            var view = UnityEngine.Object.Instantiate(Prefabs.SliderHandle, SceneViewManager.sceneRoot);
            view.Setup(direction, length, position, rotation, scale, color);

            if (binding != null)
                view.AddBinding(binding(view.props));

            view.AddBinding(view.gameObject.DestroyOnRelease());

            return view;
        }

        public static PlaneHandle PlaneHandle(Rect rect = default, Vector3 position = default, Quaternion? rotation = default, float scale = 1f, Color? color = default, Func<PlaneHandle.Props, IDisposable> binding = default)
        {
            var view = UnityEngine.Object.Instantiate(Prefabs.PlaneHandle, SceneViewManager.sceneRoot);
            view.Setup(rect, position, rotation, scale, color);

            if (binding != null)
                view.AddBinding(binding(view.props));

            view.AddBinding(view.gameObject.DestroyOnRelease());

            return view;
        }

        public static RotateHandle RotateHandle(float radius = 0.5f, Vector3? normal = default, Vector3 position = default, Quaternion? rotation = default, float scale = 1f, Color? color = default, Func<RotateHandle.Props, IDisposable> binding = default)
        {
            var view = UnityEngine.Object.Instantiate(Prefabs.RotateHandle, SceneViewManager.sceneRoot);
            view.Setup(radius, normal, position, rotation, scale, color);

            if (binding != null)
                view.AddBinding(binding(view.props));

            view.AddBinding(view.gameObject.DestroyOnRelease());

            return view;
        }
    }
}