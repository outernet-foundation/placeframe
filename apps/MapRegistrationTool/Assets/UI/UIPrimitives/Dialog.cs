using UnityEngine;

using FofX.Stateful;

using UnityEngine.UI;
using TMPro;

namespace Placeframe.MapRegistrationTool
{
    public class Dialog : Control<Dialog.Props>
    {
        public class Props : ObservableObject
        {
            public ObservablePrimitive<string> title { get; private set; }
            public ObservablePrimitive<DialogStatus> status { get; private set; }
            public ObservablePrimitive<bool> allowCancel { get; private set; }
            public ObservablePrimitive<float> minimumWidth { get; private set; }

            public Props() : base() { }

            public Props(string title = default, DialogStatus status = default, bool allowCancel = default, float minimumWidth = 500f)
            {
                this.title = new ObservablePrimitive<string>(title);
                this.status = new ObservablePrimitive<DialogStatus>(status);
                this.allowCancel = new ObservablePrimitive<bool>(allowCancel);
                this.minimumWidth = new ObservablePrimitive<float>(minimumWidth);
            }
        }

        public RectTransform content => _content;

        [SerializeField]
        private TextMeshProUGUI _title;

        [SerializeField]
        private Button _closeButton;

        [SerializeField]
        private RectTransform _content;

        [SerializeField]
        private LayoutElement _layoutElement;

        public void Setup(Props props)
            => InitializeAndBind(props);

        protected override void Bind()
        {
            AddBinding(
                _title.BindText(props.title),
                _closeButton.gameObject.BindActive(props.allowCancel),
                _closeButton.onClick.OnRaised(() => props.status.ExecuteSet(DialogStatus.Canceled)),
                props.minimumWidth.OnChange(x => _layoutElement.minWidth = x)
            );
        }
    }
}