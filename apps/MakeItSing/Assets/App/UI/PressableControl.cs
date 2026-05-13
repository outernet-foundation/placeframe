using Nessle;
using ObserveThing;

using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;

namespace Plerion.MakeItSing
{
    public struct PressableProps
    {
        public ElementProps element;
        public LayoutProps layout;
        public IValueObservable<Sprite> background;
        public ImageStyleProps backgroundStyle;
        public IValueObservable<RectOffset> padding;
        public IValueObservable<bool> interactable;
        public UnityAction onClick;
        public IListObservable<IControl> content;
    }

    [RequireComponent(typeof(Button))]
    public class PressableControl : Control<PressableProps>
    {
        public Control<ImageProps> background;
        public LayoutGroup childParent;
        private Button _button;

        protected override void SetupInternal()
        {
            _button = GetComponent<Button>();

            if (props.onClick != null)
                _button.onClick.AddListener(props.onClick);

            background.Setup(new() { sprite = props.background, style = props.backgroundStyle });

            AddBinding(
                background,
                props.element.Subscribe(this),
                props.layout.Subscribe(this),
                props.interactable?.Subscribe(x => _button.interactable = x),
                props.padding?.Subscribe(x => childParent.padding = x),
                props.content?.SubscribeAsChildren(childParent.transform)
            );
        }
    }
}