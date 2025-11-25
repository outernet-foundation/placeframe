using UnityEngine;
using UnityEngine.UI;

namespace PlerionClient.Client
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
        public Toggle recordButton => _recordButton;
        public Toggle playButton => _playButton;

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
        private Toggle _recordButton;

        [SerializeField]
        private Toggle _playButton;
    }
}