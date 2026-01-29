using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit.UI;
using UnityEngine.XR.ARFoundation;

namespace Outernet.Client
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
        public static XRUIInputModule InputModule => _instance._inputModule;
        public static GameObject XrOrigin => _instance._xrOrigin;
        public static GameObject ArSession => _instance._arSession;
        public static ARAnchorManager AnchorManager => _instance._anchorManager;

        [SerializeField]
        private CesiumForUnity.CesiumGeoreference _cesiumGeoreference;

        [SerializeField]
        private XRUIInputModule _inputModule;

        [SerializeField]
        private GameObject _xrOrigin;

        [SerializeField]
        private GameObject _arSession;

        [SerializeField]
        private ARAnchorManager _anchorManager;

        [SerializeField]
        private TilesetReference[] _tilesets;

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