using Nessle;
using UnityEngine;
using UnityEngine.UI;

namespace Plerion.MakeItSing
{
    [RequireComponent(typeof(CanvasGroup))]
    public class AnimatedListElementContainer : MonoBehaviour, ILayoutElement, ILayoutGroup
    {
        public float minWidth { get; private set; }
        public float preferredWidth { get; private set; }
        public float flexibleWidth { get; private set; }
        public float minHeight { get; private set; }
        public float preferredHeight { get; private set; }
        public float flexibleHeight { get; private set; }
        public int layoutPriority => 0;

        public float alpha
        {
            get => _fadeGroup.alpha;
            set => _fadeGroup.alpha = value;
        }

        public IControl body => _body;

        private IControl _body;
        private CanvasGroup _fadeGroup;

        private void Awake()
        {
            _fadeGroup = GetComponent<CanvasGroup>();
        }

        public void Setup(IControl body)
        {
            _body = body;

            minWidth = LayoutUtility.GetMinWidth(_body.rectTransform);
            preferredWidth = LayoutUtility.GetPreferredWidth(_body.rectTransform);
            flexibleWidth = LayoutUtility.GetFlexibleWidth(_body.rectTransform);

            minHeight = LayoutUtility.GetMinHeight(_body.rectTransform);
            preferredHeight = LayoutUtility.GetPreferredHeight(_body.rectTransform);
            flexibleHeight = LayoutUtility.GetFlexibleHeight(_body.rectTransform);
        }

        public void CalculateLayoutInputHorizontal()
        {
            if (_body == null)
            {
                minWidth = 0;
                preferredWidth = 0;
                flexibleWidth = 0;
                return;
            }

            foreach (var element in _body.rectTransform.GetComponents<ILayoutElement>())
                element.CalculateLayoutInputHorizontal();

            minWidth = LayoutUtility.GetMinWidth(_body.rectTransform);
            preferredWidth = LayoutUtility.GetPreferredWidth(_body.rectTransform);
            flexibleWidth = LayoutUtility.GetFlexibleWidth(_body.rectTransform);
        }

        public void CalculateLayoutInputVertical()
        {
            if (_body == null)
            {
                minHeight = 0;
                preferredHeight = 0;
                flexibleHeight = 0;
                return;
            }

            foreach (var element in _body.rectTransform.GetComponents<ILayoutElement>())
                element.CalculateLayoutInputVertical();

            minHeight = LayoutUtility.GetMinHeight(_body.rectTransform);
            preferredHeight = LayoutUtility.GetPreferredHeight(_body.rectTransform);
            flexibleHeight = LayoutUtility.GetFlexibleHeight(_body.rectTransform);
        }

        public void SetLayoutHorizontal()
        {
            if (_body == null)
                return;

            _body.rectTransform.SetSizeWithCurrentAnchors(RectTransform.Axis.Horizontal, ((RectTransform)transform).rect.width);
        }

        public void SetLayoutVertical()
        {
            if (_body == null)
                return;

            _body.rectTransform.SetSizeWithCurrentAnchors(RectTransform.Axis.Vertical, ((RectTransform)transform).rect.height);
        }
    }
}