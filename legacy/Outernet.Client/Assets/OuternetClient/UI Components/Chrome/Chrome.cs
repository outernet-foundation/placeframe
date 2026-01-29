using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using R3;
using System;

namespace Outernet.Client
{
    [ExecuteAlways]
    [RequireComponent(typeof(RectTransform))]
    public class Chrome : UIBehaviour
    {
        private const float minimumWidth = 0.6f;

        [SerializeField]
        private Button _closeButton;
        public LayoutGroup content;
        public PanelView panelView;

        public Subject<Vector2> dimensionsSubject = new Subject<Vector2>();

        private Vector3 _dimensions;
        public Vector2 dimensions
        {
            get => _dimensions;
            set
            {
                if (rectTransform.localScale.x == 0 || rectTransform.localScale.y == 0)
                {
                    rectTransform.sizeDelta = Vector2.zero;
                    return;
                }

                _dimensions = Vector2.Max(value, minimumDimensions);
                rectTransform.sizeDelta = dimensions / rectTransform.localScale;
                dimensionsSubject.OnNext(_dimensions);
            }
        }

        public Vector2 minimumDimensions
        {
            get
            {
                if (content == null) return Vector2.zero;

                var minimumDimensions = Vector2.Scale(new Vector2(content.minWidth, content.minHeight), rectTransform.localScale);
                minimumDimensions.x = Mathf.Max(minimumDimensions.x, minimumWidth);
                return minimumDimensions;
            }
        }

        public bool allowCarry = true;
        public bool allowResize = true;

        public UnityEvent onCarryStarted;
        public UnityEvent onCarryEnded;
        public UnityEvent onResizeStarted;
        public UnityEvent onResizeEnded;
        public UnityEvent onCloseSelected => _closeButton.onClick;

        public float resizeHandleSpacing;
        public float lineHandleHeightPadding;
        public ResizeHandle lowerLeftCorner;
        public ResizeHandle lowerRightCorner;
        public ResizeHandle upperLeftCorner;
        public ResizeHandle upperRightCorner;
        public ResizeHandle leftEdge;
        public ResizeHandle rightEdge;
        public ResizeHandle topEdge;
        public CarryHandle carryHandle;

        private RectTransform rectTransform => (RectTransform)transform;

        protected override void Awake()
        {
            lowerLeftCorner.normalizedPosition = new Vector3(-0.5f, -0.5f, 0);
            lowerRightCorner.normalizedPosition = new Vector3(0.5f, -0.5f, 0);
            upperLeftCorner.normalizedPosition = new Vector3(-0.5f, 0.5f, 0);
            upperRightCorner.normalizedPosition = new Vector3(0.5f, 0.5f, 0);

            lowerLeftCorner.offset = new Vector3(-resizeHandleSpacing, -resizeHandleSpacing, 0);
            lowerRightCorner.offset = new Vector3(resizeHandleSpacing, -resizeHandleSpacing, 0);
            upperLeftCorner.offset = new Vector3(-resizeHandleSpacing, resizeHandleSpacing, 0);
            upperRightCorner.offset = new Vector3(resizeHandleSpacing, resizeHandleSpacing, 0);

            leftEdge.normalizedPosition = new Vector3(-0.5f, 0, 0);
            rightEdge.normalizedPosition = new Vector3(0.5f, 0, 0);
            topEdge.normalizedPosition = new Vector3(0, 0.5f, 0);
            carryHandle.normalizedPosition = new Vector3(0, -0.5f, 0);

            leftEdge.offset = new Vector3(-resizeHandleSpacing, 0, 0);
            rightEdge.offset = new Vector3(resizeHandleSpacing, 0, 0);
            topEdge.offset = new Vector3(0, resizeHandleSpacing, 0);
            carryHandle.offset = new Vector3(0, -resizeHandleSpacing, 0);

            dimensions = rectTransform.sizeDelta * rectTransform.localScale;
        }

        private void Update()
        {
            // Hack to handle content minimum dimensions changing
            dimensions = dimensions;
        }

        protected override void OnRectTransformDimensionsChange()
        {
            panelView.dimensions = new Vector2(rectTransform.rect.width, rectTransform.rect.height);
        }

        protected override void OnTransformParentChanged()
        {
            OnCanvasGroupChanged();
        }
    }
}