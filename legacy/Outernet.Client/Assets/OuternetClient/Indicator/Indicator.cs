using UnityEngine;
using UnityEngine.Rendering;
using R3;
using System;

namespace Outernet.Client
{
    public class Indicator : MonoBehaviour
    {
        private const float peripheralIndicatorScale = 0.1f;
        private const float peripheralIndicatorDistanceFromViewport = 1f;
        private const float toPeripherySmoothTime = 0.2f;
        private const float toInViewSmoothTime = 0.3f;
        private const float insetMargin = 0.15f;

        public GameObject model;
        public MeshRenderer meshRenderer;

        private bool isUser;
        private Vector3 rotationVelocity;
        private float scaleVelocity;
        private float perceivedScaleVelocity;

        private IDisposable subscriptions;

        public void Initialize(bool isUser)
        {
            this.isUser = isUser;

            if (isUser)
            {
                meshRenderer.material.color = Color.blue;
            }
            else
            {
                meshRenderer.material.color = Color.green;
            }

            // In an AR app (or at least an Android Mobile AR app, the only platform I can detect this
            // behavior on), the only way to get the latest camera viewport is to use a
            // RenderPipelineManager.beginCameraRendering callback; doing this in Update or LateUpdate
            // will result in the viewport being one frame behind, resulting in laggy indicator movement
            //
            // Solution adapted for URP from this issue:
            // https://github.com/Unity-Technologies/arfoundation-samples/issues/417
            subscriptions = Observable
                .FromEvent<Action<ScriptableRenderContext, Camera>>(
                    handler => (context, camera) => handler(),
                    handler => RenderPipelineManager.beginCameraRendering += handler,
                    handler => RenderPipelineManager.beginCameraRendering -= handler)
                .Subscribe(_ => UpdateIndicator());
        }

        public void Terminate()
        {
            subscriptions.Dispose();

            PrefabSystem.Destroy(this);
        }

        void UpdateIndicator()
        {
            meshRenderer.enabled = App.state.settings.showIndicators.value;

            // Consider the indicator as always in view if the system menu says to not animate indicators
            if ((!Settings.animateNodeIndicators && !isUser) || (!Settings.animateUserIndicators && isUser))
            {
                transform.position = transform.parent.position;

                // Point the models up vector at the camera, so the indicator face is always facing the user
                // var targetRotationUp2 = (Camera.main.transform.position - transform.position).normalized;
                var targetRotationUp2 = transform.parent.forward;
                var targetRotationForward2 = Vector3.Cross(targetRotationUp2, Vector3.Cross(-Vector3.up, targetRotationUp2));

                if (targetRotationForward2 == Vector3.zero)
                {
                    targetRotationForward2 = Vector3.forward;
                }

                transform.rotation = Quaternion.LookRotation(targetRotationForward2, targetRotationUp2);
                return;
            }

            // If the target is too far away, don't animate the indicator
            if (Vector3.Distance(Camera.main.transform.position, transform.parent.position) > 100)
            {
                transform.position = transform.parent.position;
                return;
            }

            Vector3 direction = transform.parent.position - Camera.main.transform.position;
            bool occluded = Physics.Raycast(
                new Ray(Camera.main.transform.position, direction),
                out RaycastHit _,
                direction.magnitude,
                LayerMask.GetMask("Buildings"));

            // If the target is occluded, don't animate the indicator
            if (occluded)
            {
                transform.position = transform.parent.position;
                return;
            }

            // Position of the target with respect to the camera, normalized to the viewport
            Vector3 targetPositionViewportSpace = Camera.main.WorldToViewportPoint(transform.parent.position);

            // Is the indicator within the camera's field of view?
            var inView =
                targetPositionViewportSpace.x > insetMargin && targetPositionViewportSpace.x < 1 - insetMargin &&
                targetPositionViewportSpace.y > insetMargin && targetPositionViewportSpace.y < 1 - insetMargin;

            // If the target is behind the camera, the viewport position is flipped, so flip it back
            if (targetPositionViewportSpace.z < 0)
            {
                targetPositionViewportSpace.x = 1 - targetPositionViewportSpace.x;
                targetPositionViewportSpace.y = 1 - targetPositionViewportSpace.y;
            }

            // If the target is not in view, or is "in view" but behind the camera, intersect the ray from the camera to the 
            // target with the viewport edges and use the intersection point as the target position
            if (!inView || targetPositionViewportSpace.z < 0)
            {
                var intersection = IntersectRayRectangle(
                    new Vector2(0.5f, 0.5f),
                    new Vector2(targetPositionViewportSpace.x - 0.5f, targetPositionViewportSpace.y - 0.5f),
                    new Rect(0, 0, 1, 1)
                );

                targetPositionViewportSpace.x = Mathf.Clamp(intersection.x, insetMargin, 1 - insetMargin);
                targetPositionViewportSpace.y = Mathf.Clamp(intersection.y, insetMargin, 1 - insetMargin);

                // If the target is behind the camera, it is not actually in view
                inView = false;
            }

            // If the target is behind the user and was clamped to the top or bottom of the viewport, clamp it to the left or right corner;
            // Leaving it at the top or bottom would direct the user to look "past" straight up or straight down, i.e. rotate their head about the x-axis beyond vertical
            var userForward = Vector3.ProjectOnPlane(Camera.main.transform.forward, Vector3.up).normalized;
            var userPlane = new Plane(userForward, Camera.main.transform.position);
            if (!userPlane.GetSide(transform.parent.position) && (targetPositionViewportSpace.y == 0 || targetPositionViewportSpace.y == 1))
            {
                targetPositionViewportSpace.x = targetPositionViewportSpace.x < 0.5f ? 0 : 1;
            }

            // Smooth at different rates depending on whether we are moving to the viewport periphery, or back into normal view
            var smoothTime = inView ? toInViewSmoothTime : toPeripherySmoothTime;

            // Current perceived scale (scale adjusted for distance from camera)
            var currentPerceivedScale = transform.localScale.x / Camera.main.WorldToViewportPoint(transform.position).z;

            // Interpolate scale
            var targetScale = inView ? transform.parent.localScale.x : peripheralIndicatorScale;
            transform.localScale = Vector3.one * Mathf.SmoothDamp(transform.localScale.x, targetScale, ref scaleVelocity, smoothTime);

            // Interpolate perceived scale
            var targetPerceivedScale = inView ? transform.parent.localScale.x / targetPositionViewportSpace.z : targetScale / peripheralIndicatorDistanceFromViewport;
            var newPerceivedScale = Mathf.SmoothDamp(currentPerceivedScale, targetPerceivedScale, ref perceivedScaleVelocity, smoothTime);

            // We know our scale and our perceived scale, so we can calculate our new position
            targetPositionViewportSpace.z = transform.localScale.x / newPerceivedScale;
            transform.position = Camera.main.ViewportToWorldPoint(targetPositionViewportSpace);

            //// Interpolate rotation
            //// Note: the local transform for the indicator model has the pointy bit of the 
            //// indicator facing forward, and the face of the indicator facing up

            // Point the models up vector at the camera, so the indicator face is always facing the user
            var targetRotationUp = inView ? transform.parent.forward : (Camera.main.transform.position - transform.position).normalized;
            // Point the models forward at the target if it is out of view, or straight down if it is in view
            var targetRotationForward = inView ? -Vector3.up : (transform.parent.position - transform.position).normalized;

            // Maintain the up vector by reprojecting the forward vector orthogonal to the up vector;
            // We do this to ensure the indicator face is directly facing the user
            targetRotationForward = Vector3.Cross(targetRotationUp, Vector3.Cross(targetRotationForward, targetRotationUp));

            // Interpolate
            if (targetRotationForward != Vector3.zero)
            {
                var targetRotation = Quaternion.LookRotation(targetRotationForward, targetRotationUp);
                transform.rotation = MathUtils.SmoothDampQuaternion(transform.rotation, targetRotation, ref rotationVelocity, smoothTime);
            }
        }

        private Vector2 IntersectRayRectangle(Vector2 rayOrigin, Vector2 rayDirection, Rect rect)
        {
            var topLeft = new Vector2(rect.xMin, rect.yMax);
            var topRight = new Vector2(rect.xMax, rect.yMax);
            var bottomRight = new Vector2(rect.xMax, rect.yMin);
            var bottomLeft = new Vector2(rect.xMin, rect.yMin);

            Vector2 intersection;

            if (IntersectRayLineSegment(rayOrigin, rayDirection, topLeft, topRight, out intersection) ||
                IntersectRayLineSegment(rayOrigin, rayDirection, topRight, bottomRight, out intersection) ||
                IntersectRayLineSegment(rayOrigin, rayDirection, bottomRight, bottomLeft, out intersection) ||
                IntersectRayLineSegment(rayOrigin, rayDirection, bottomLeft, topLeft, out intersection))
            {
                return intersection;
            }

            return Vector2.zero;
        }

        private bool IntersectRayLineSegment(Vector2 rayOrigin, Vector2 rayDirection, Vector2 segmentStart, Vector2 segmentEnd, out Vector2 intersection)
        {
            float a1 = rayDirection.y;
            float b1 = -rayDirection.x;
            float c1 = a1 * rayOrigin.x + b1 * rayOrigin.y;

            float a2 = segmentEnd.y - segmentStart.y;
            float b2 = segmentStart.x - segmentEnd.x;
            float c2 = a2 * segmentStart.x + b2 * segmentStart.y;

            float determinant = a1 * b2 - a2 * b1;

            if (determinant == 0)
            {
                intersection = Vector2.zero;
                return false;
            }

            float x = (b2 * c1 - b1 * c2) / determinant;
            float y = (a1 * c2 - a2 * c1) / determinant;
            intersection = new Vector2(x, y);

            bool onRay = IsPointOnRay(intersection, rayOrigin, rayDirection);
            bool onSegment = IsPointOnLineSegment(intersection, segmentStart, segmentEnd);

            return onRay && onSegment;
        }

        private bool IsPointOnLineSegment(Vector2 point, Vector2 lineStart, Vector2 lineEnd)
        {
            float minX = Mathf.Min(lineStart.x, lineEnd.x);
            float maxX = Mathf.Max(lineStart.x, lineEnd.x);
            float minY = Mathf.Min(lineStart.y, lineEnd.y);
            float maxY = Mathf.Max(lineStart.y, lineEnd.y);

            return point.x >= minX && point.x <= maxX && point.y >= minY && point.y <= maxY;
        }

        private bool IsPointOnRay(Vector2 point, Vector2 rayOrigin, Vector2 rayDirection)
        {
            Vector2 directionToPoint = point - rayOrigin;
            float dotProduct = Vector2.Dot(directionToPoint, rayDirection);
            return dotProduct > 0;
        }
    }
}