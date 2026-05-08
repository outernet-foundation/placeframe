using UnityEngine;
using UnityEngine.XR.ARFoundation;
using CesiumForUnity;

namespace Plerion.MakeItSing
{
    public class SceneReferences : MonoBehaviour
    {
        public static SceneReferences _instance;

        public static ARAnchorManager ARAnchorManager => _instance._arAnchorManager;
        public static ARCameraManager ARCameraManager => _instance._arCameraManager;
        public static GameObject[] Controllers => _instance._controllers;
        public static CesiumGeoreference CesiumGeoreference => _instance._cesiumGeoreference;
        public static Cesium3DTileset GroundTileset => _instance._groundTileset;

        [SerializeField]
        private ARAnchorManager _arAnchorManager;

        [SerializeField]
        private ARCameraManager _arCameraManager;

        [SerializeField]
        private CesiumGeoreference _cesiumGeoreference;

        [SerializeField]
        private Cesium3DTileset _groundTileset;

        [SerializeField]
        private GameObject[] _controllers;

        public void Initialize()
        {
            _instance = this;
        }
    }
}