using UnityEngine;
using UnityEngine.XR.ARFoundation;

namespace Plerion.MakeItSing
{
    public class SceneReferences : MonoBehaviour
    {
        public static SceneReferences _instance;

        public static ARAnchorManager ARAnchorManager => _instance._arAnchorManager;
        public static ARCameraManager ARCameraManager => _instance._arCameraManager;

        [SerializeField]
        private ARAnchorManager _arAnchorManager;

        [SerializeField]
        private ARCameraManager _arCameraManager;

        public void Initialize()
        {
            _instance = this;
        }
    }
}