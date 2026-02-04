using System.Collections.Generic;
using CesiumForUnity;
using UnityEngine;

namespace Placeframe.MapRegistrationTool
{
    public class SceneReferences : MonoBehaviour
    {
        private static SceneReferences _instance;

        [System.Serializable]
        public class TilesetReference
        {
            public string name;
            public GameObject reference;
        }

        public static CesiumForUnity.CesiumGeoreference CesiumGeoreference => _instance._cesiumGeoreference;
        public static IEnumerable<TilesetReference> Tilesets => _instance._tilesets;
        public static Cesium3DTileset GroundTileset => _instance._groundTileset;

        [SerializeField]
        private CesiumForUnity.CesiumGeoreference _cesiumGeoreference;

        [SerializeField]
        private TilesetReference[] _tilesets;
        [SerializeField]
        private Cesium3DTileset _groundTileset;

        private void Awake()
        {
            if (_instance != this)
                Initialize();
        }

        public void Initialize()
        {
            if (_instance != null && _instance != this)
            {
                Destroy(this);
                throw new System.Exception($"Only one instance of {nameof(SceneReferences)} allowed in the scene at a time!");
            }

            _instance = this;
        }
    }
}