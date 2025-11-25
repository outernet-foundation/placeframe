using UnityEngine;
using UnityEngine.XR.ARFoundation;

namespace PlerionClient.Client
{
    public class SceneReferences : MonoBehaviour
    {
        public static ARCameraManager ARCameraManager => _instance._arCameraManager;

        private static SceneReferences _instance;

        [SerializeField]
        private ARCameraManager _arCameraManager;

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
                throw new System.Exception($"Only one instance of {nameof(SceneReferences)} is allowed in the scene at a time.");
            }

            _instance = this;
        }
    }
}