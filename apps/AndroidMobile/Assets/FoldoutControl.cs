using Nessle;
using ObserveThing;
using UnityEngine.Events;

namespace PlerionClient.Client
{
    public struct FoldoutProps
    {
        public TextProps label;
        public IValueObservable<bool> interactable;
        public IValueObservable<bool> isOpen;
        public LayoutGroupProps childrenLayout;
        public UnityAction<bool> isOpenChanged;
    }

    public class FoldoutControl : Control<FoldoutProps>
    {
        public Control<ToggleProps> toggle;
        public Control<TextProps> label;
        public Control<LayoutGroupProps> layout;

        protected override void SetupInternal()
        {
            label.Setup(props.label);
            layout.Setup(props.childrenLayout);
            toggle.Setup(new ToggleProps()
            {
                value = props.isOpen,
                interactable = props.interactable,
                onValueChanged = x =>
                {
                    layout.gameObject.SetActive(x);
                    props.isOpenChanged?.Invoke(x);
                }
            });
        }
    }
}