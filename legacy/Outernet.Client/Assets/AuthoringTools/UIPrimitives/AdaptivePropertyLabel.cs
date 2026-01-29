using UnityEngine;
using UnityEngine.UI;

namespace Outernet.Client.AuthoringTools
{
    public class AdaptivePropertyLabel : PropertyLabel
    {
        public RectTransform wideModeContentRegion;
        public RectTransform narrowModeContentRegion;
        private bool _isDirty;

        private void Awake()
        {
            wideModeContentRegion.GetMonoBehaviourEventHelper().onRectTransformDimesionsChanged.OnRaised(_ => HandleDimensionsChanged());
            content.GetMonoBehaviourEventHelper().onRectTransformDimesionsChanged.OnRaised(_ => HandleDimensionsChanged());
        }

        private void HandleDimensionsChanged()
        {
            _isDirty = true;
        }

        private void Update()
        {
            if (_isDirty)
            {
                _isDirty = false;
                UpdateControlParent();
            }
        }

        private void UpdateControlParent()
        {
            var tooWide = LayoutUtility.GetPreferredWidth((RectTransform)content.transform) > wideModeContentRegion.rect.width;
            var tooTall = LayoutUtility.GetPreferredHeight((RectTransform)content.transform) > wideModeContentRegion.rect.height;
            var contentParent = tooWide || tooTall ? narrowModeContentRegion : wideModeContentRegion;

            narrowModeContentRegion.gameObject.SetActive(contentParent == narrowModeContentRegion);

            if (content.transform.parent != contentParent)
                content.transform.SetParent(contentParent, false);
        }
    }
}