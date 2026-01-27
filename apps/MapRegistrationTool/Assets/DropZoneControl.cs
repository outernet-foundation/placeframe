using Nessle;
using UnityEngine;

using ObserveThing;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Outernet.MapRegistrationTool
{
    public struct DropZoneProps
    {
        public ElementProps element;
        public LayoutProps layout;
        public IValueObservable<Sprite> highlight;
        public ImageStyleProps highlightStyle;
        public System.Action<GameObject> onDropReceived;
        public System.Func<GameObject, bool> validateDrop;
    }

    [RequireComponent(typeof(Image))]
    public class DropZoneControl : Nessle.Control<DropZoneProps>, IDropHandler, IPointerEnterHandler, IPointerExitHandler
    {
        private Nessle.Control<ImageProps> _highlight;
        private ListObservable<GameObject> _potentialDrops = new ListObservable<GameObject>();

        protected override void SetupInternal()
        {
            _highlight = gameObject.GetOrAddComponent<Nessle.Control<ImageProps>, ImageControl>();
            _highlight.Setup(new()
            {
                element = { active = _potentialDrops.CountDynamic().SelectDynamic(x => x > 0) },
                sprite = props.highlight,
                style = props.highlightStyle
            });

            AddBinding(
                props.element.Subscribe(this),
                props.layout.Subscribe(this),
                _highlight
            );
        }

        public void OnDrop(PointerEventData eventData)
        {
            props.onDropReceived?.Invoke(eventData.pointerDrag);
        }

        public void OnPointerEnter(PointerEventData eventData)
        {
            if (eventData.pointerDrag == null)
                return;

            if (props.validateDrop?.Invoke(eventData.pointerDrag) ?? true)
                _potentialDrops.Add(eventData.pointerDrag);
        }

        public void OnPointerExit(PointerEventData eventData)
        {
            if (eventData.pointerDrag == null)
                return;

            _potentialDrops.Remove(eventData.pointerDrag);
        }
    }
}