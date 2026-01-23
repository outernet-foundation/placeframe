#if AUTHORING_TOOLS_ENABLED
using UnityEngine;
using UnityEngine.InputSystem;

namespace Outernet.Client
{
    public class Platform : MonoBehaviour
    {
        private void Awake()
        {
            var camera = Camera.main;
            camera.clearFlags = CameraClearFlags.Skybox;

            if (camera.TryGetComponent(out UnityEngine.InputSystem.XR.TrackedPoseDriver poseDriver))
                poseDriver.enabled = false;
        }
    }
}
#endif