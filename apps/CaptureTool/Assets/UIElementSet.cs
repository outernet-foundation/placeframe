using Nessle;
using UnityEngine;
using UnityEngine.UI;

namespace Placeframe.Client
{
    [CreateAssetMenu(fileName = "UIElementSet", menuName = "Scriptable Objects/UIElementSet")]
    public class UIElementSet : ScriptableObject
    {
        public Color foregroundColor => _foregroundColor;
        public Color midgroundColor => _midgroundColor;
        public Color backgroundColor => _backgroundColor;
        public Color deepBackgroundColor => _deepBackgroundColor;
        public Color highlightColor => _highlightColor;
        public Sprite roundedRect => _roundedRect;
        public Sprite moreMenuSprite => _moreMenuSprite;
        public Control<ToggleProps> recordButton => _recordButton;
        public Control<ToggleProps> playButton => _playButton;
        public Control<FoldoutProps> foldout => _foldout;
        public Control<ButtonProps> roundButton => _roundButton;

        [SerializeField]
        private Color _foregroundColor;

        [SerializeField]
        private Color _midgroundColor;

        [SerializeField]
        private Color _backgroundColor;

        [SerializeField]
        private Color _deepBackgroundColor;

        [SerializeField]
        private Color _highlightColor;

        [SerializeField]
        private Sprite _roundedRect;

        [SerializeField]
        private Sprite _moreMenuSprite;

        [SerializeField]
        private Control<ToggleProps> _recordButton;

        [SerializeField]
        private Control<ToggleProps> _playButton;

        [SerializeField]
        private Control<FoldoutProps> _foldout;

        [SerializeField]
        private Control<ButtonProps> _roundButton;
    }
}