using System;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Nessle
{
    public class ScrollingDropdownControl : UnityComponentControl<TMP_Dropdown>, IValueControl<int>
    {
        public IUnityComponentControl<Image> background { get; }
        public IUnityComponentControl<TextMeshProUGUI> captionText { get; }
        public IUnityComponentControl<Image> arrow { get; private set; }
        public ScrollRectControl template { get; }
        public IUnityComponentControl<Toggle> itemToggle { get; }
        public IUnityComponentControl<Image> itemBackground { get; }
        public IUnityComponentControl<TextMeshProUGUI> itemLabel { get; }
        public IUnityComponentControl<Image> itemCheckmark { get; }

        public event Action<int> onChange;
        public int value
        {
            get => _value;
            set
            {
                if (_value == value)
                    return;

                _value = value;
                onChange.Invoke(value);
            }
        }

        private int _value;

        public ScrollingDropdownControl(
            IUnityComponentControl<Image> background = default,
            IUnityComponentControl<TextMeshProUGUI> captionText = default,
            IUnityComponentControl<Image> arrow = default,
            ScrollRectControl template = default,
            IUnityComponentControl<Toggle> itemToggle = default,
            IUnityComponentControl<Image> itemBackground = default,
            IUnityComponentControl<TextMeshProUGUI> itemLabel = default,
            IUnityComponentControl<Image> itemCheckmark = default
        ) : base(UIBuilder.GameObject<TMP_Dropdown>())
        {
            this.Children(
                this.background = background ?? new UnityComponentControl<Image>(gameObject.AddComponent<Image>()),
                this.captionText = captionText ?? UIBuilder.Label().FillParent().Alignment(TextAlignmentOptions.CaplineLeft).Margin(new Vector4(12, 0, 0, 0)),
                this.arrow = arrow ?? UIBuilder.Image().Sprite(UIResources.ArrowDown).AnchorToRight().SizeDelta(new Vector2(10, 10)).PreserveAspect(true).LocalPosition(new Vector3(-15, -1.2f, 0)),
                this.template = template ?? UIBuilder.ScrollRect().Style(x =>
                {
                    x.EnableHorizontalScroll(false)
                        .FillParentWidth()
                        .SizeDelta(new Vector2(0, 150))
                        .SetPivot(new Vector2(0, 1))
                        .AnchorToBottom();

                    x.content
                        .FitContentVertical(ContentSizeFitter.FitMode.PreferredSize)
                        .SetPivot(new Vector2(0.5f, 1))
                        .AnchorToTop()
                        .FillParentWidth()
                        .SizeDelta(new Vector2(0, 150));

                }).Content(
                    UIBuilder.VerticalLayout().ControlChildSize(true).ChildForceExpandWidth(true).Children( //Content
                        this.itemToggle = itemToggle ?? UIBuilder.ComponentControl<Toggle>().FillParentWidth().PreferredHeight(30).Children(
                            this.itemBackground = itemBackground ?? UIBuilder.Image().FillParent(),
                            this.itemCheckmark = itemCheckmark ?? UIBuilder.Image().Sprite(UIResources.Checkmark).PreserveAspect(true).AnchorToRight().SetPivot(new Vector2(1f, 0.5f)).SizeDelta(new Vector2(15, 15)).LocalPosition(new Vector3(-10, 0, 0)),
                            this.itemLabel = itemLabel ?? UIBuilder.Label().Alignment(TextAlignmentOptions.CaplineLeft).Margin(new Vector4(10, 0, 0, 0)).FillParent()
                        )
                    )
                )
            );

            this.itemToggle.component.graphic = this.itemCheckmark.component;
            this.itemToggle.component.targetGraphic = this.itemBackground.component;

            component.targetGraphic = this.background.component;
            component.template = this.template.rectTransform;
            component.captionText = this.captionText.component;
            component.itemText = this.itemLabel.component;

            this.template.gameObject.SetActive(false);
        }
    }
}
