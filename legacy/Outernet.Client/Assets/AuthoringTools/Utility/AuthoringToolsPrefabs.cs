using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace Outernet.Client.AuthoringTools
{
    [CreateAssetMenu]
    public class AuthoringToolsPrefabs : ScriptableObject
    {
        public static Camera Camera => _instance._camera;
        public static Canvas Canvas => _instance._canvas;
        public static SystemMenu SystemMenu => _instance._systemMenu;
        public static AuthoringToolsUI UI => _instance._ui;
        public static AuthoringToolsSceneViewManager SceneViewManager => _instance._sceneViewManager;
        public static Scrim Scrim => _instance._scrim;
        public static AuthoringToolsMap SceneMap => _instance._sceneMap;
        public static AuthoringToolsNode AuthoringToolsNode => _instance._authoringToolsNode;
        public static Color SelectedColor => _instance._selectedColor;
        public static TextMeshProUGUI Text => _instance._text;
        public static EditableLabel EditableLabel => _instance._editableLabel;
        public static TMP_InputField InputField => _instance._inputField;
        public static TMP_InputField InputRegion => _instance._inputRegion;
        public static HorizontalLayoutGroup HorizontalLayout => _instance._horizontalLayout;
        public static VerticalLayoutGroup VerticalLayout => _instance._verticalLayout;
        public static PropertyLabel TightPropertyLabel => _instance._tightPropertyLabel;
        public static PropertyLabel PropertyLabel => _instance._propertyLabel;
        public static AdaptivePropertyLabel AdaptivePropertyLabel => _instance._adaptivePropertyLabel;
        public static Toggle Toggle => _instance._toggle;
        public static TMP_Dropdown Dropdown => _instance._dropdown;
        public static Foldout Foldout => _instance._foldout;
        public static PropertyLabel Header => _instance._header;
        public static LabelButton Button => _instance._button;
        public static ListElementContainer ListElement => _instance._listElement;
        public static Image Window => _instance._window;
        public static Dialog Dialog => _instance._dialog;
        public static ScrollRect ScrollRect => _instance._scrollRect;
        public static Mesh TorusMesh => _instance._torusMesh;
        public static Mesh HalfTorusMesh => _instance._halfTorusMesh;
        public static Mesh CylinderMesh => _instance._cylinderMesh;
        public static Mesh ConeMesh => _instance._coneMesh;
        public static Mesh QuadMesh => _instance._quadMesh;
        public static Material GizmoMaterial => _instance._gizmoMaterial;
        public static Material GizmoMaterialNoZTest => _instance._gizmoMaterialNoZTest;
        public static SliderHandle SliderHandle => _instance._sliderHandle;
        public static RotateHandle RotateHandle => _instance._rotateHandle;
        public static PlaneHandle PlaneHandle => _instance._planeHandle;

        private static AuthoringToolsPrefabs _instance;

        [Header("General")]
        [SerializeField]
        private Camera _camera;

        [SerializeField]
        private Canvas _canvas;

        [SerializeField]
        private SystemMenu _systemMenu;

        [SerializeField]
        private AuthoringToolsUI _ui;

        [SerializeField]
        private AuthoringToolsSceneViewManager _sceneViewManager;

        [SerializeField]
        private Scrim _scrim;

        [Header("Scene")]
        [SerializeField]
        private AuthoringToolsMap _sceneMap;

        [SerializeField]
        private AuthoringToolsNode _authoringToolsNode;

        [Header("UI Primitives")]
        [SerializeField]
        private TextMeshProUGUI _text;
        [SerializeField]
        private EditableLabel _editableLabel;

        [SerializeField]
        private TMP_InputField _inputField;

        [SerializeField]
        private TMP_InputField _inputRegion;

        [SerializeField]
        private HorizontalLayoutGroup _horizontalLayout;

        [SerializeField]
        private VerticalLayoutGroup _verticalLayout;

        [SerializeField]
        private PropertyLabel _tightPropertyLabel;

        [SerializeField]
        private PropertyLabel _propertyLabel;

        [SerializeField]
        private AdaptivePropertyLabel _adaptivePropertyLabel;

        [SerializeField]
        private Foldout _foldout;

        [SerializeField]
        private PropertyLabel _header;

        [SerializeField]
        private Toggle _toggle;

        [SerializeField]
        private TMP_Dropdown _dropdown;

        [SerializeField]
        private LabelButton _button;

        [SerializeField]
        private ListElementContainer _listElement;

        [SerializeField]
        private Image _window;

        [SerializeField]
        private Dialog _dialog;

        [SerializeField]
        private ScrollRect _scrollRect;

        [SerializeField]
        private Color _selectedColor;

        [Header("Runtime Gizmo Assets")]
        [SerializeField]
        private Mesh _torusMesh;

        [SerializeField]
        private Mesh _halfTorusMesh;

        [SerializeField]
        private Mesh _cylinderMesh;

        [SerializeField]
        private Mesh _coneMesh;

        [SerializeField]
        private Mesh _quadMesh;

        [SerializeField]
        private Material _gizmoMaterial;

        [SerializeField]
        private Material _gizmoMaterialNoZTest;

        [SerializeField]
        private SliderHandle _sliderHandle;

        [SerializeField]
        private RotateHandle _rotateHandle;

        [SerializeField]
        private PlaneHandle _planeHandle;

        public static void Initialize(string resourcePath)
        {
            if (_instance != null)
                throw new System.Exception($"{nameof(AuthoringToolsPrefabs)} already loaded!");

            // Use resources here so we don't have to reference the prefab in the editor
            _instance = Resources.Load<AuthoringToolsPrefabs>(resourcePath);
        }
    }
}