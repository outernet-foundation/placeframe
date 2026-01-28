using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using System.Linq;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;
using UnityEngine.XR.Management;
using MagicLeap.OpenXR.Subsystems;
using MagicLeap.Android;

namespace Outernet.Client
{
    static public class PlaneDetector
    {
        static private ARPlaneManager planeManager;

        const int maxResults = 100;
        const float minPlaneArea = 0.25f;

        static public HashSet<ARPlane> Planes { get; private set; } = new HashSet<ARPlane>();

        static public async UniTask Initialize()
        {
            await UniTask.WaitUntil(() => XRGeneralSettings.Instance?.Manager?.activeLoader?.GetLoadedSubsystem<XRPlaneSubsystem>() != null);

            planeManager = GameObject.FindFirstObjectByType<ARPlaneManager>();
            planeManager.trackablesChanged.AddListener(args =>
            {
                foreach (ARPlane plane in args.added)
                {
                    Log.Info($"Plane detected: {plane.trackableId}");
                    Planes.Add(plane);
                }

                foreach (ARPlane plane in args.removed.Select(removed => removed.Value))
                {
                    Log.Info($"Plane removed: {plane.trackableId}");
                    Planes.Remove(plane);
                }
            });

#if MAGIC_LEAP
            Permissions.RequestPermission(
                Permissions.SpatialMapping,
                OnPermissionGranted,
                OnPermissionDenied,
                OnPermissionDenied);
#endif
        }

        static public void Update()
        {
#if MAGIC_LEAP
            if (planeManager != null && planeManager.enabled)
            {
                var newQuery = new MLXrPlaneSubsystem.PlanesQuery
                {
                    Flags = planeManager.requestedDetectionMode.ToMLXrQueryFlags() | MLXrPlaneSubsystem.MLPlanesQueryFlags.SemanticFloor,
                    BoundsCenter = Camera.main.transform.position,
                    BoundsRotation = Camera.main.transform.rotation,
                    BoundsExtents = Vector3.one * 20f,
                    MaxResults = maxResults,
                    MinPlaneArea = minPlaneArea
                };

                MLXrPlaneSubsystem.Query = newQuery;
            }
#endif
        }

#if MAGIC_LEAP
        static private void OnPermissionGranted(string permission)
        {
            planeManager.enabled = true;
        }

        static private void OnPermissionDenied(string permission)
        {
            // TODO: Show error message
        }
#endif
    }
}