using UnityEngine;
using TMPro;
using UnityEngine.UI;

namespace Nessle
{
    [CreateAssetMenu(fileName = "UIResources", menuName = "Scriptable Objects/UIResources")]
    public class UIResources : ScriptableObject
    {
        public static Sprite RoundedBox => _instance._roundedBox;
        public static Sprite ArrowDown => _instance._arrowDown;
        public static Sprite ArrowRight => _instance._arrowRight;
        public static Sprite Checkmark => _instance._checkmark;
        public static Color PanelColor => _instance._panelColor;
        public static Color ButtonColor => _instance._buttonColor;
        public static Color InputFieldColor => _instance._inputFieldColor;
        public static Color PanelHeaderColor => _instance._panelHeaderColor;
        public static Color SectionHeaderColor => _instance._sectionHeaderColor;
        public static Color TextColor => _instance._textColor;
        public static Color ScrollBarHandleColor => _instance._scrollBarHandleColor;
        public static Color ScrollBarBackgroundColor => _instance._scrollBarBackgroundColor;

        private static UIResources _instance => Resources.Load<UIResources>("UIResources");

        [SerializeField] private Sprite _roundedBox;
        [SerializeField] private Sprite _arrowDown;
        [SerializeField] private Sprite _arrowRight;
        [SerializeField] private Sprite _checkmark;
        [SerializeField] public Color _panelColor;
        [SerializeField] public Color _buttonColor;
        [SerializeField] public Color _inputFieldColor;
        [SerializeField] public Color _panelHeaderColor;
        [SerializeField] public Color _sectionHeaderColor;
        [SerializeField] public Color _textColor;
        [SerializeField] public Color _scrollBarHandleColor;
        [SerializeField] public Color _scrollBarBackgroundColor;
    }
}