using System;

using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;

using FofX.Stateful;

using TMPro;
using FofX;

namespace Outernet.Client.AuthoringTools
{
    public class LoadingBarDialog : Control<LoadingBarDialog.Props>
    {
        public class Props : ObservableObject
        {
            public ObservablePrimitive<string> description { get; private set; }
            public ObservablePrimitive<float> progress { get; private set; }
            public ObservablePrimitive<bool> allowCancel { get; private set; }
            public ObservablePrimitive<bool> isDone { get; private set; }

            public Props() : base() { }

            public Props(string description = default, float progress = default, bool allowCancel = default, bool isDone = default)
            {
                this.description = new ObservablePrimitive<string>(description);
                this.progress = new ObservablePrimitive<float>(progress);
                this.allowCancel = new ObservablePrimitive<bool>(allowCancel);
                this.isDone = new ObservablePrimitive<bool>(isDone);
            }
        }

        public UnityEvent onFinishSelected;
        public UnityEvent onCancelSelected;

        [SerializeField]
        private TextMeshProUGUI _label;

        [SerializeField]
        private Slider _progressBar;

        [SerializeField]
        private LabelButton _cancelButton;

        private TaskHandle _progressAnimation = TaskHandle.Complete;

        public override void Setup()
            => InitializeAndBind(new Props());

        public void Setup(string description = default, float progress = default, bool allowCancel = default, bool isDone = default)
            => InitializeAndBind(new Props(description, progress, allowCancel, isDone));

        protected override void Bind()
        {
            AddBinding(
                _label.BindText(props.description),
                _cancelButton.gameObject.BindActive(props.allowCancel),
                props.isDone.OnChange(x => _cancelButton.label.text = x ? "Finish" : "Cancel"),
                _cancelButton.button.onClick.OnRaised(() => (props.isDone.value ? onFinishSelected : onCancelSelected).Invoke()),
                props.progress.OnChange(progress =>
                {
                    _progressAnimation.Cancel();
                    _progressAnimation = TaskHandle.Execute(token => Tween.FloatEaseInOut(_progressBar.value, progress, x => _progressBar.value = x, token));
                })
            );
        }
    }
}