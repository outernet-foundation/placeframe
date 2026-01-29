using UnityEngine;
using UnityEngine.UIElements;
using UnityEngine.XR.ARFoundation;

namespace Outernet.Client
{
    public class PrefabSystem : MonoBehaviour
    {
        private static PrefabSystem _instance;
        public static ARSession arSession => _instance._arSession;
        public static Indicator indicatorView => _instance._indicatorViewPrefab;
        public static LocalUser localUser => _instance._localUserPrefab;
        public static RemoteUser remoteUser => _instance._remoteUserPrefab;
        public static CitationView citationView => _instance._citationViewPrefab;
        public static ImageView imageView => _instance._imageViewPrefab;
        public static SettingsPanel systemUIView => _instance._settingsPanelPrefab;
        public static Stub systemUIViewMobile => _instance._settingsPanelMobilePrefab;
        public static SettingsSystemMobile settingsSystemMobile => _instance._settingsSystemMobilePrefab;
        public static UIDocument cesiumCreditSystemUI => _instance._cesiumCreditSystemUIPrefab;
        public static Toast toast => _instance._toastPrefab;
        public static NodeImageView nodeImageView => _instance._nodeImageView;
        public static NodeTextView nodeTextView => _instance._nodeTextView;
        public static ClientNode clientNode => _instance._clientNode;
        public static ClientExhibit clientExhibit => _instance._clientExhibit;
        public static ClientIndicator clientIndicator => _instance._clientIndicator;

        [SerializeField]
        private ARSession _arSession;

        [SerializeField]
        private Indicator _indicatorViewPrefab;

        [SerializeField]
        private LocalUser _localUserPrefab;

        [SerializeField]
        private RemoteUser _remoteUserPrefab;

        [SerializeField]
        private CitationView _citationViewPrefab;

        [SerializeField]
        private ImageView _imageViewPrefab;

        [SerializeField]
        private SettingsPanel _settingsPanelPrefab;

        [SerializeField]
        private Stub _settingsPanelMobilePrefab;

        [SerializeField]
        private SettingsSystemMobile _settingsSystemMobilePrefab;

        [SerializeField]
        private UIDocument _cesiumCreditSystemUIPrefab;

        [SerializeField]
        private Toast _toastPrefab;

        [SerializeField]
        private ClientNode _clientNode;

        [SerializeField]
        private ClientIndicator _clientIndicator;

        [SerializeField]
        private NodeImageView _nodeImageView;

        [SerializeField]
        private NodeTextView _nodeTextView;

        [SerializeField]
        private ClientExhibit _clientExhibit;

        private void Awake()
        {
            if (_instance != null && _instance != this)
                throw new System.Exception($"An instance of {nameof(PrefabSystem)} already exists in the scene.");

            _instance = this;
        }

        static public T Create<T>(T prefab, Transform parent = null) where T : MonoBehaviour
        {
            return GameObject.Instantiate(prefab, parent);
        }

        static public void Destroy<T>(T monoBehaviour) where T : MonoBehaviour
        {
            GameObject.Destroy(monoBehaviour.gameObject);
        }

        static public void Destroy(GameObject gameObject)
        {
            GameObject.Destroy(gameObject);
        }
    }
}