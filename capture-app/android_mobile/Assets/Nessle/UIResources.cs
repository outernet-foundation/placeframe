using UnityEngine;
using TMPro;
using UnityEngine.UI;

namespace Nessle
{
    [CreateAssetMenu(fileName = "UIResources", menuName = "Scriptable Objects/UIResources")]
    public class UIResources : ScriptableObject
    {
        public static TextMeshProUGUI Text => _instance._text;
        public static TMP_InputField InputField => _instance._inputField;
        public static Scrollbar Scrollbar => _instance._scrollbar;
        public static ScrollRect ScrollRect => _instance._scrollRect;
        public static TMP_Dropdown Dropdown => _instance._dropdown;
        public static Button Button => _instance._button;
        public static HorizontalLayoutGroup HorizontalLayout => _instance._horizontalLayout;
        public static VerticalLayoutGroup VerticalLayout => _instance._verticalLayout;
        public static Toggle Toggle => _instance._toggle;
        public static Slider Slider => _instance._slider;

        private static UIResources _instance => Resources.Load<UIResources>("UIResources");

        [SerializeField] private TextMeshProUGUI _text;
        [SerializeField] private TMP_InputField _inputField;
        [SerializeField] private Scrollbar _scrollbar;
        [SerializeField] private ScrollRect _scrollRect;
        [SerializeField] private TMP_Dropdown _dropdown;
        [SerializeField] private Button _button;
        [SerializeField] private HorizontalLayoutGroup _horizontalLayout;
        [SerializeField] private VerticalLayoutGroup _verticalLayout;
        [SerializeField] private Toggle _toggle;
        [SerializeField] private Slider _slider;
    }
}