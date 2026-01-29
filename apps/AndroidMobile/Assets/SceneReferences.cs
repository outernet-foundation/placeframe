using UnityEngine;
using UnityEngine.XR.ARFoundation;

namespace Placeframe.Client
{
    public class SceneReferences : MonoBehaviour
    {
        public static ARCameraManager ARCameraManager => _instance._arCameraManager;
        public static ARAnchorManager ARAnchorManager => _instance._arAnchorManager;

        private static SceneReferences _instance;

        [SerializeField]
        private ARCameraManager _arCameraManager;

        [SerializeField]
        private ARAnchorManager _arAnchorManager;

        private void Awake()
        {
            Initialize();
        }

        private void OnDestroy()
        {
            if (_instance == this)
                _instance = null;
        }

        public void Initialize()
        {
            if (_instance != null && _instance != this)
            {
                Destroy(this);
                throw new System.Exception(
                    $"Only one instance of {nameof(SceneReferences)} is allowed in the scene at a time."
                );
            }

            _instance = this;
        }
    }
}
