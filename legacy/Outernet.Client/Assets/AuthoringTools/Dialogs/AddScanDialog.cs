using System;
using FofX.Stateful;
using UnityEngine.UI;
using UnityEngine.Events;
using TMPro;
// using SFB;

namespace Outernet.Client.AuthoringTools
{
    public class AddScanDialog : Control<AddScanDialog.Props>
    {
        public class Props : ObservableObject
        {
            public ObservablePrimitive<string> mapPath { get; private set; }
            public ObservablePrimitive<string> mapName { get; private set; }

            public Props() : base() { }

            public Props(string mapPath = default, string mapName = default)
            {
                this.mapPath = new ObservablePrimitive<string>(mapPath);
                this.mapName = new ObservablePrimitive<string>(mapName);
            }
        }

        public UnityEvent<string, string> onComplete = new UnityEvent<string, string>();
        public UnityEvent onCanceled = new UnityEvent();

        public TMP_InputField mapNameInputField;
        public TMP_InputField mapPathInputField;
        public Button selectMapPathButton;
        public Button completeButton;
        public Button cancelButton;

        private void Awake()
        {
            completeButton.onClick.AddListener(() => onComplete.Invoke(props.mapName.value, props.mapPath.value));
            cancelButton.onClick.AddListener(() => onCanceled.Invoke());
        }

        public override void Setup()
            => InitializeAndBind(new Props());

        public void Setup(string mapPath = default, string mapName = default)
            => InitializeAndBind(new Props(mapPath, mapName));

        protected override void Bind()
        {
            AddBinding(
                mapNameInputField.BindInput(props.mapName),
                mapPathInputField.BindInput(props.mapPath),
                selectMapPathButton.onClick.OnRaised(() =>
                {
                    // StandaloneFileBrowser had to be removed, pending fixing the plugin
                    // var paths = StandaloneFileBrowser.OpenFilePanel("Select Scan", "", "b2g", false);
                    // if (paths.Length > 0)
                    //     ExecuteAction(x => x.mapPath.value = paths[0]);
                }),
                Bindings.Observer(
                    _ => completeButton.interactable =
                        !string.IsNullOrEmpty(props.mapName.value) &&
                        !string.IsNullOrEmpty(props.mapPath.value),
                    ObservationScope.Self,
                    props.mapName,
                    props.mapPath
                )
            );
        }
    }
}