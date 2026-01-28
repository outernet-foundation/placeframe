#if !UNITY_EDITOR && MAGIC_LEAP
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR;

namespace Outernet.Client
{
    class Platform : MonoBehaviour
    {
        private void Awake()
        {
            DynamicFocusDistanceSystem.Initialize();
        }

        private void Start()
        {
            List<XRDisplaySubsystem> xRDisplays = new List<XRDisplaySubsystem>();

            SubsystemManager.GetSubsystems(xRDisplays);
            if (xRDisplays.Count > 0)
            {
                xRDisplays[0].foveatedRenderingLevel = 1.0f;
                xRDisplays[0].foveatedRenderingFlags = XRDisplaySubsystem.FoveatedRenderingFlags.GazeAllowed;
            }
        }

        private void Update()
        {
            DynamicFocusDistanceSystem.Update();
        }
    }
}
#endif