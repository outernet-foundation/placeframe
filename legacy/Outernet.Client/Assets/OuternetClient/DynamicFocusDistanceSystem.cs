using System.Linq;
using MagicLeap.Android;
using MagicLeap.OpenXR.Features;
using UnityEngine.XR.OpenXR;
using UnityEngine.XR.OpenXR.Features.Interactions;
using R3;
using UnityEngine;
using UnityEngine.XR.MagicLeap;
using UnityEngine.XR;

namespace Outernet.Client
{
    public static class DynamicFocusDistanceSystem
    {
        private const float sphereCastRadius = .075f;

        private static bool permissionGranted = false;
        private static MagicLeapRenderingExtensionsFeature renderFeature;
        private static RaycastHit[] hitsBuffer = new RaycastHit[30];
        private static GameObject hitPointDebugVisual = null;

        static public void Initialize()
        {
            renderFeature = OpenXRSettings.Instance.GetFeature<MagicLeapRenderingExtensionsFeature>();

            hitPointDebugVisual = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            hitPointDebugVisual.SetActive(false);
            hitPointDebugVisual.GetComponent<Renderer>().material = Resources.Load<Material>("SphereCastHitPoint");
            hitPointDebugVisual.transform.localScale = Vector3.one * .02f;
            GameObject.Destroy(hitPointDebugVisual.GetComponent<Collider>());

            Permissions.RequestPermission(
                Permissions.EyeTracking,
                _ => HandlePermissionResult(true),
                _ => HandlePermissionResult(false),
                _ => HandlePermissionResult(false));
        }

        static public void Update()
        {
            if (App.ClientID == null) return;

            // If we are not in dynamic focus distance mode, set the focus distance to the default value of 10
            if (!App.State_Old.settingsDynamicFocusDistance.Value)
            {
                Camera.main.stereoConvergence = 10f;
                renderFeature.FocusDistance = 10f;
                return;
            }

            hitPointDebugVisual.SetActive(App.State_Old.settingsShowEyeDebug.Value);

            // If we don't have permission, we are done
            if (!permissionGranted) return;

            var eyeTrackingDevices = InputSubsystem.Utils.FindMagicLeapDevice(
                InputDeviceCharacteristics.EyeTracking |
                InputDeviceCharacteristics.TrackedDevice);

            // If we don't have valid eye tracking data, we are done
            if (!eyeTrackingDevices.isValid ||
                !eyeTrackingDevices.TryGetFeatureValue(CommonUsages.isTracked, out var isTracked) ||
                !isTracked ||
                !eyeTrackingDevices.TryGetFeatureValue(EyeTrackingUsages.gazePosition, out var position) ||
                !eyeTrackingDevices.TryGetFeatureValue(EyeTrackingUsages.gazeRotation, out var rotation))
            {
                return;
            }

            int hitCount = Physics.SphereCastNonAlloc(
                new Ray(position, rotation * Vector3.forward),
                sphereCastRadius,
                hitsBuffer,
                Camera.main.farClipPlane,
                ~(1 << LayerMask.NameToLayer("Buildings")));

            // If eye tracking data does not hit any object, we are done
            if (hitCount == 0) return;

            // Find the closest hit point
            var hitPoint = hitsBuffer.Take(hitCount).OrderBy(h => h.distance).FirstOrDefault().point;

            // Update the hit point debug visual
            hitPointDebugVisual.transform.position = hitPoint;

            // Set the focus distance and camera steroConvergence to the distance from the camera to the hit point
            renderFeature.FocusDistance = Camera.main.stereoConvergence =
                Vector3.Dot(rotation * Vector3.forward, hitPoint - position);
            //Mathf.Max(Camera.main.nearClipPlane, Vector3.Dot(hitPoint, Camera.main.transform.forward));
        }

        static private void HandlePermissionResult(bool granted)
        {
            permissionGranted = granted;

            if (granted)
            {
                Log.Info(LogGroup.Permissions, "Eye tracking permission granted.");
            }
            else
            {
                Log.Warn(LogGroup.Permissions, "Eye tracking permission denied.");
            }
        }
    }
}
